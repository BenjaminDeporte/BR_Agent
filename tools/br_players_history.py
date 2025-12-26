import requests
import json
import datetime
import pandas as pd
import os
from typing import Any, Optional
from smolagents.tools import Tool
from pathlib import Path


def _load_br_keys() -> dict:
    """Load BR API credentials from project root .brkeys."""
    keys_path = Path(__file__).resolve().parent.parent / ".brkeys"
    with keys_path.open(mode="r") as f:
        return json.load(f)

#----------------------------------------------------------------
#
#  ANALYTICAL TOOL 
#  Get a structured view (Python object) of the history of a 
#  player, from the BR API
#
#  this is for the CodeAgent to be able to process the data
#
#----------------------------------------------------------------

   
class GetPlayerHistoryData(Tool):
    name = "get_player_history_data"
    description = (
        "Returns structured player history data for a player as a list of dictionaries. "
        "Each dictionnary contains details about a specific entry in the player's history, including :"
        " - id : the entry identification number"
        " - date : the date of the entry"
        " - event : the event description"
        "This output is intended for computation and analysis."
    )
    inputs = {
        'player_id' : 
            {'type': 'integer', 'description': 'the identification number ID of the player'}
    }
    output_type = "object"

    def __init__(self,
                 player_id=None,
                 team_name: Optional[str] = None,
                 **kwargs
                 ):
        super().__init__()
        try:
            pwd = _load_br_keys()
            self.MY_TEAM_ID = pwd['MY_TEAM_ID']
            self.ACCESS_KEY = pwd['ACCESS_KEY']
            self.DEV_ID = pwd.get('DEV_ID')
            self.DEV_KEY = pwd.get('DEV_KEY')
            self.MY_MEMBER_ID = pwd.get('MY_MEMBER_ID')
        except Exception as e:
            print("Erreur lors de la lecture du fichier .brkeys :", e)
            raise e
        
        self.team_name = team_name
        self.player_id = player_id
        self.response = None
        self.filename = ""
        self.BR_API="http://classic-api.blackoutrugby.com"
        
        
    def forward(self, player_id: int) -> list[dict]:
        """
        method to get the list of players in a team from the BR API.

        - renvoie une string avec la liste des joueurs
        - écrit l'objet response dans la property correspondante self.response
        """
        
        payload = {
            "d" : self.DEV_ID,
            "dk" : self.DEV_KEY,
            "r" : "ph",  # Player History
            "playerid" : player_id,
            "m" : self.MY_MEMBER_ID,
            # "teamid" : team_id,
            "mk" : self.ACCESS_KEY,
            "json" : 1
        }
        
        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")

        return data.get("entries", [])
    
    
#----------------------------------------------------------------
# DISPLAY TOOL - Get a human-readable summary of players in a team from the BR API
#----------------------------------------------------------------

class GetPlayerHistoryInfo(Tool):
    name = "get_player_history_info"
    description = (
        "Returns a formatted, human-readable text summary of the history of a player"
        "This tool is intended for display and information only, not for "
        "programmatic analysis or computation."
        "This tool returns formatted text and is not suitable for programmatic analysis."
    )

    inputs = {
        "player_id": {
            "type": "integer",
            "description": "The identification number ID of the player"
        }
    }

    output_type = "string"   # TERMINAL TOOL
    
    def __init__(self,
                 player_id=None,
                 team_name: Optional[str] = None,
                 **kwargs
                 ):
        super().__init__()
        try:
            pwd = _load_br_keys()
            self.MY_TEAM_ID = pwd['MY_TEAM_ID']
            self.ACCESS_KEY = pwd['ACCESS_KEY']
            self.DEV_ID = pwd.get('DEV_ID')
            self.DEV_KEY = pwd.get('DEV_KEY')
            self.MY_MEMBER_ID = pwd.get('MY_MEMBER_ID')
        except Exception as e:
            print("Erreur lors de la lecture du fichier .brkeys :", e)
            raise e
        
        self.team_name = team_name
        self.player_id = player_id
        self.response = None
        self.filename = ""
        self.BR_API="http://classic-api.blackoutrugby.com"

    def forward(self, player_id: int) -> str:
        payload = {
            "d": self.DEV_ID,
            "dk": self.DEV_KEY,
            "r": "ph",  # Player History
            "m": self.MY_MEMBER_ID,
            "playerid": player_id,
            "mk": self.ACCESS_KEY,
            "json": 1
        }

        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")

        player_history = data.get("entries", [])

        if not player_history:
            return f"No player history found for player {player_id}."

        lines = []
        lines.append(f"Player {player_id} — History\n")
        lines.append(f"Total entries: {len(player_history)}\n")
        for entry in player_history:
            lines.append(
                f"ID: {entry.get('id')} | Date: {entry.get('date')} | Event: {entry.get('event')}"
            )

        return "\n".join(lines)
    
    
#--------------------------------------------------------------------
# TOOL TO GET TRAINING HISTORY DATA
#----------------------------------------------------

class GetTeamTrainingHistoryData(Tool):
    name = "get_team_training_history_data"
    description = (
        "Returns structured team training history data for a team as .... "
        "The output is composed of a list of two dictionnaries : "
        " - team : containing details about the team"
        "   the team dictionnary includes :"
        "     - key 'skill' : list of the four skills that were trained that particular week"
        " - players : containing details about the players' training history"
        "   the players dictionary is composed as such :"
        "   - each key is a player ID, and the value is a dictionary with the following details :"
        "       - id : the player identification number"
        "       - drops : list of drops during training"
        "       - pops : list of pops during training"
        "       - csr : dictionary with changes in CSR"
        "       - energy : dictionary with changes in Energy"
        "This output is intended for computation and analysis."
    )
    inputs = {
        'team_id' : {'type': 'integer', 'description': 'the identification number ID of the team'},
        'season' : {'type': 'integer', 'description': 'the season number'},  
        'round' : {'type': 'integer', 'description': 'the round number within the season'},
    }
    output_type = "object"

    def __init__(self,
                 team_id=None,
                 team_name: Optional[str] = None,
                 **kwargs
                 ):
        super().__init__()
        try:
            pwd = _load_br_keys()
            self.MY_TEAM_ID = pwd['MY_TEAM_ID']
            self.ACCESS_KEY = pwd['ACCESS_KEY']
            self.DEV_ID = pwd.get('DEV_ID')
            self.DEV_KEY = pwd.get('DEV_KEY')
            self.MY_MEMBER_ID = pwd.get('MY_MEMBER_ID')
        except Exception as e:
            print("Erreur lors de la lecture du fichier .brkeys :", e)
            raise e
        
        self.team_name = team_name
        self.team_id = team_id
        self.response = None
        self.filename = ""
        self.BR_API="http://classic-api.blackoutrugby.com"
        
        
    def forward(self, team_id: int, season: int, round: int) -> list[dict]:
        """
        method to get the list of players in a team from the BR API.

        - renvoie une string avec la liste des joueurs
        - écrit l'objet response dans la property correspondante self.response
        """
        
        payload = {
            "d" : self.DEV_ID,
            "dk" : self.DEV_KEY,
            "r" : "tr",  # Team Training History
            "teamid" : team_id,
            "season" : season,
            "round" : round,
            "m" : self.MY_MEMBER_ID,
            # "teamid" : team_id,
            "mk" : self.ACCESS_KEY,
            "json" : 1
        }
        
        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")
        
        report = data.get("report", {}).get('report', {})
        report_team = report.get('team', {})
        report_players = report.get('individual', {}).get('players', {})

        return [report_team, report_players]
    
#--------------------------------------------------"

if __name__ == "__main__":
    mytool = GetTeamTrainingHistoryData()
    r = mytool.forward(team_id=57796, season=59, round=13)
    print(r)