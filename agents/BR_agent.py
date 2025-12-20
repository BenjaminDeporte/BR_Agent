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
    openai_model = LiteLLMModel(model_id="openai/gpt-4o-mini")
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

get_players_info_from_team_tool = GetPlayersInfoFromTeam()
get_players_data_from_team_tool = GetPlayersDataFromTeam()

brtools = [
    get_players_info_from_team_tool,
    get_players_data_from_team_tool,
]

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
        *brtools
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
#    "APP"
#-------------------------------------------------------------------------------------

print(f"Agent is powered by: {agent.model.model_id}")
print("-" * 25)

print(f"Gradio version is {gr.__version__}")

def chat_with_agent(message, history):
    history = history or []

    # run agent
    response = str(agent.run(message))

    # append user
    history.append({"role": "user", "content": message})
    # append assistant
    history.append({"role": "assistant", "content": response})

    # return history for Chatbot, and empty string for Textbox to clear it
    return history, ""

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

demo.launch()