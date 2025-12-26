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
#  ANALYTICAL TOOL - Get a structured list of players in a team from the BR API
#  this is for the CodeAgent to be able to process the data
#
#----------------------------------------------------------------

   
class GetPlayersDataFromYouthTeam(Tool):
    name = "get_players_data_from_youth_team"
    description = (
        "Returns structured player data for a youth U20 team as a list of dictionaries. "
        "Each dictionary contains at least: name (str), age (int), nationality (str), "
        "csr (int), energy (int), skills (dict), contract_until (str). "
        "This output is intended for computation and analysis."
    )
    inputs = {
        'team_id' : 
            {'type': 'integer', 'description': 'the identification number ID of the team'}
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
        
        
    def forward(self, team_id: int) -> list[dict]:
        """
        method to get the list of players in a youth team from the BR API.

        - renvoie une string avec la liste des joueurs
        - écrit l'objet response dans la property correspondante self.response
        """
        
        payload = {
            "d" : self.DEV_ID,
            "dk" : self.DEV_KEY,
            "r" : "p",
            "m" : self.MY_MEMBER_ID,
            "teamid" : team_id,
            "mk" : self.ACCESS_KEY,
            "json" : 1,
            "youth" : 1
        }
        
        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")

        players_raw = data.get("players", {})

        players = []
        for p in players_raw.values():
            players.append({
                "id": p.get("id"),
                "team_id": p.get("teamid"),
                "first_name": p.get("fname"),
                "last_name": p.get("lname"),
                "name": p.get("name"),
                "age": int(p.get("age")),
                "nationality": p.get("nationality"),
                # "salary": int(p.get("salary", 0)),
                "form": int(p.get("form", 0)),
                "aggression": int(p.get("aggression", 0)),
                "discipline": int(p.get("discipline", 0)),
                "leadership": int(p.get("leadership", 0)),
                "experience": int(p.get("experience", 0)),
                "weight": int(p.get("weight", 0)),
                "height": int(p.get("height", 0)),
                # "csr": int(p.get("csr", 0)),
                "energy": int(p.get("energy", 0)),
                'scouting_stars_used':int(p.get('scouting_stars_used')),
                "skills": {
                    "stamina": p.get("stamina"),
                    "handling": p.get("handling"),
                    "attack": p.get("attack"),
                    "defense": p.get("defense"),
                    "technique": p.get("technique"),
                    "strength": p.get("strength"),
                    "jumping": p.get("jumping"),
                    "speed": p.get("speed"),
                    "agility": p.get("agility"),
                    "kicking": p.get("kicking"),
                },
                # "contract_until": p.get("contract", "").split("T")[0]
            })

        return players
    
    
#----------------------------------------------------------------
# DISPLAY TOOL - Get a human-readable summary of players in a team from the BR API
#----------------------------------------------------------------

class GetPlayersInfoFromYouthTeam(Tool):
    name = "get_players_info_from_youth_team"
    description = (
        "Returns a formatted, human-readable text summary of all players in a youth U20 team. "
        "This tool is intended for display and information only, not for "
        "programmatic analysis or computation."
        "This tool returns formatted text and is not suitable for programmatic analysis."
    )

    inputs = {
        "team_id": {
            "type": "integer",
            "description": "The identification number ID of the team"
        }
    }

    output_type = "string"   # TERMINAL TOOL
    
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

    def forward(self, team_id: int) -> str:
        payload = {
            "d": self.DEV_ID,
            "dk": self.DEV_KEY,
            "r": "p",
            "m": self.MY_MEMBER_ID,
            "teamid": team_id,
            "mk": self.ACCESS_KEY,
            "json": 1,
            "youth": 1
        }

        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")

        players = data.get("players", {})

        if not players:
            return f"No players found for team {team_id}."

        lines = []
        lines.append(f"Team {team_id} — Players\n")
        lines.append(f"Total players: {len(players)}\n")

        for p in players.values():
            lines.append(
                f"{p.get('fname', '?')} {p.get('lname', '?')}\n"
                f" Age {p.get('age', '?')} Form {p.get('form', '?')} Agg {p.get('aggression', '?')} Disc {p.get('discipline', '?')}"
                f" Lead {p.get('leadership', '?')} Exp {p.get('experience', '?')}\n"
                f" Energy: {p.get('energy', '?')}\n"
                f" Weight: {p.get('weight', '?')} Height: {p.get('height', '?')}\n"
                f" Scouting Stars Used: {p.get('scouting_stars_used', '?')}\n"
                f"  Skills: Sta {p.get('stamina', '?')}, "
                f"Han {p.get('handling', '?')}, "
                f"Att {p.get('attack', '?')}, "
                f"Def {p.get('defense', '?')}, "
                f"Tec {p.get('technique', '?')}, "
                f"Str {p.get('strength', '?')}, "
                f"Jmp {p.get('jumping', '?')}, "
                f"Spd {p.get('speed', '?')}, "
                f"Agi {p.get('agility', '?')}, "
                f"Kic {p.get('kicking', '?')}\n"
            )

        return "\n".join(lines)

#--------------------------------------------------------------------

if __name__ == "__main__":
    mytool = GetPlayersDataFromYouthTeam()
    print(mytool.forward(team_id=57796))  # Example team ID