import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from smolagents import LiteLLMModel, CodeAgent, DuckDuckGoSearchTool, tool
import datetime, pytz
import gradio as gr

# Ensure project root (parent of agents/) is on sys.path so sibling packages like tools import correctly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
#----------------------------------------------------------------------------------
#       LOAD ENVIRONMENT VARIABLES CONTAINING API KEYS
#----------------------------------------------------------------------------------

# --- Step 1: Load environment variables from the .env file ---
# load_dotenv() searches for the .env file in the current directory and loads
# the key/value pairs into the environment (os.environ).
load_dotenv() 

# --- Step 2: Access the API Key (Optional Check) ---
# You can optionally check if the variable was loaded correctly, 
# but models often do this check internally.
# openai_key = os.getenv("OPENAI_API_KEY")

# if openai_key:
#     print("Open API Key loaded successfully. Length:", len(openai_key))
# else:
#     print("WARNING: OPENAI_API_KEY not found in environment.")

# --- Step 3: Use the Model (it automatically reads the environment) ---
# LiteLLMModel automatically picks up the OPENAI_API_KEY from os.environ

#----------------------------------------------------------------------------------
#       CHECK THAT MODELS CAN BE ACCESSED
#----------------------------------------------------------------------------------

# OPEN AI -------------------------------------------------------------------------
try:
    openai_model = LiteLLMModel(model_id="openai/gpt-3.5-turbo")
    print(f"Open AI modèle chargé")
except Exception as e:
    print(f"Pb chargement modèle Open AI")
    
# GOOGLE MODEL --------------------------------------------------------------------
try:
    gemini_model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")
    print(f"Google Gemini AI modèle chargé")
except Exception as e:
    print(f"Pb chargement modèle Gemini")
    
# MISTRAL --------------------------------------------------------------------------
try:
    mistral_model = LiteLLMModel(model_id="mistral/mistral-small-latest")
    print(f"Mistral AI modèle chargé")
except Exception as e:
    print(f"Pb chargement modèle Mistral")

#------------------------------------------------------------------------------------
#       TOOLS DEFINITION - GENERAL TOOLS
#------------------------------------------------------------------------------------

@tool
def get_current_time_in_timezone(timezone: str) -> str:
    """A tool that fetches the current local time in a specified timezone.
    Args:
        timezone: A string representing a valid timezone (e.g., 'America/New_York').
    """
    try:
        # Create timezone object
        tz = pytz.timezone(timezone)
        # Get current time in that timezone
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        return f"Error fetching time for timezone '{timezone}': {str(e)}"
    
#------------------------------------------------------------------------------------
#       TOOLS DEFINITION - BLACKOUT RUGBY TOOLS
#------------------------------------------------------------------------------------

from tools.br_players_in_team import GetPlayersInfoFromTeam, GetPlayersDataFromTeam
from tools.br_team_memory import (
    LoadTeamSnapshot,
    CompareTeamSnapshots,
    SaveTeamSnapshot,
    ReportTeamChanges
)
from tools.br_players_in_youth_team import GetPlayersDataFromYouthTeam, GetPlayersInfoFromYouthTeam
from tools.br_youth_team_memory import (
    LoadYouthTeamSnapshot,
    CompareYouthTeamSnapshots,
    SaveYouthTeamSnapshot,
    ReportYouthTeamChanges
)
from tools.br_players_history import GetPlayerHistoryData, GetPlayerHistoryInfo, GetTeamTrainingHistoryData
from tools.br_utils import Converter_From_Season_Round_Day_to_Date_INFO, Converter_From_Season_Round_Day_to_Date_DATA

brtools = [
    GetPlayersInfoFromTeam(),
    GetPlayersDataFromTeam(),
    GetPlayersInfoFromYouthTeam(),
    GetPlayersDataFromYouthTeam()
]
br_memory_tools = [
    LoadTeamSnapshot(),
    ReportTeamChanges(),
    CompareTeamSnapshots(),
    SaveTeamSnapshot(),
    LoadYouthTeamSnapshot(),
    ReportYouthTeamChanges(),
    CompareYouthTeamSnapshots(),
    SaveYouthTeamSnapshot()
]
br_history_tools = [
    GetPlayerHistoryData(),
    GetPlayerHistoryInfo(),
    GetTeamTrainingHistoryData()
]
br_utils_tools = [
    Converter_From_Season_Round_Day_to_Date_INFO(),
    Converter_From_Season_Round_Day_to_Date_DATA()
]

#-------------------------------------------------------------------------------------
#        SHORT-TERM/CONVERSATION MEMORY (HOME MADE)
#-------------------------------------------------------------------------------------

from chat_memory import ChatSessionHistory

chat_history = ChatSessionHistory()

#------------------------------------------------------------------------------------
#        AGENTS
#------------------------------------------------------------------------------------

# Read system prompt from file
with open("/home/benjamin/Folders_Python/BR_Agent/agents/prompts/instructions.txt", "r", encoding="utf-8") as f:
    instructions = f.read()
    
# implement the agent

agent = CodeAgent(
    tools=[
        get_current_time_in_timezone,
        *brtools,
        *br_memory_tools,
        *br_history_tools,
        *br_utils_tools
    ], 
    model=mistral_model,
    max_steps=5,
    verbosity_level=1,
    additional_authorized_imports=[
        "pytz",
        "datetime"
        ],
    instructions=instructions
)

#-------------------------------------------------------------------------------------
#    GIVE SOME INFO ON WHAT'S RUNNING IN THE APP
#-------------------------------------------------------------------------------------

print(f"Agent is powered by: {agent.model.model_id}")
print("-" * 25)

print(f"Gradio version is {gr.__version__}")

#-------------------------------------------------------------------------------------
#    GRADIO INTERFACE
#-------------------------------------------------------------------------------------

# this is the home-made conversion normalizer from agents outputs 
# to strings suitable for UI display in Gradio
from agents.output_adapter import normalize_agent_output

# the chat engine per say
def chat_with_agent(message, history):
    
    # ------- manage in-chat memory -------------------------------------------
    
    # 1. build lightweight context for agent from in-chat memory (e.g., last 5 exchanges)
    context = ""
    for msg in chat_history.get_history()[-6:]:  # last 6 messages (3 exchanges)
        # emphasize role in capital letters
        context += f"[{msg['role'].upper()}]\n{msg['content']}\n\n"

    # 2. add user message to history
    chat_history.add_user_message(message)
        
    # 3. build combined prompt to send to agent
    combined_prompt = f"""
    Conversation context:
    {context}
    Current user message:
    {message}
    """
          
    # 4. get agent response
    try:
        raw_response = agent.run(combined_prompt)
        response = normalize_agent_output(raw_response)
    except Exception as e:
        response = f"An error occurred while processing your request: {str(e)}"
    
    # add agent message to in-chat memory
    chat_history.add_agent_message(response)
    
    #----------------------------------------------------------------------------
    # build Gradio-compatible history
    history = history or []
    history.append({"role": "user", "content": message}) # append user message
    history.append({"role": "assistant", "content": response})     # append assistant response

    # return history for Chatbot, and empty string for Textbox to clear it
    return history, ""

#------------ build Gradio app interface ------------------------
with gr.Blocks() as demo:
    gr.Markdown("## 🧠 smolagents BlackoutRugby Assistant")

    chatbot = gr.Chatbot()
    
    msg = gr.Textbox(
        placeholder="Ask something…",
        show_label=False
    )

    msg.submit(
        chat_with_agent,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]  # second output is the textbox to clear
    )
    
    # --- cosmetic ---
    # Inject auto-scroll JS
    gr.HTML("""
    <script>
    const chatObserver = new MutationObserver(() => {
      const chat = document.querySelector("#chatbot");
      if (chat) {
        chat.scrollTop = chat.scrollHeight;
      }
    });
    chatObserver.observe(document.body, {
      childList: true,
      subtree: true
    });
    </script>
    """)

demo.launch()