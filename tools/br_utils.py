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

   
class Converter_From_Season_Round_Day_to_Date_DATA(Tool):
    name = "date_converter_from_season_round_day_to_date_data"
    description = (
        "Returns the date (in YYYY-MM-DD) format) of a given Season Round Day as a datetime.date object"
    )
    inputs = {
        'season': {'type': 'integer', 'description': 'the season number'},
        'round': {'type': 'integer', 'description': 'the round number'},
        'day': {'type': 'integer', 'description': 'the day number within the round'}
    }
    output_type = "object" # datetime.date

    def __init__(self,
                 season=None,
                 round=None,
                 day=None,
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
        
        self.season = season
        self.round = round
        self.day = day
        self.response = None
        self.filename = ""
        self.BR_API="http://classic-api.blackoutrugby.com"
        
        
    def forward(self, season: int, round: int, day: int) -> datetime.date:
        """
        method to compute the date from season, round, day
        :param season: the season number
        :param round: the round number
        :param day: the day number within the round
        :return: date in YYYY-MM-DD format
        """
        
        payload = {
            "d" : self.DEV_ID,
            "dk" : self.DEV_KEY,
            "r" : "dt",  # date tool
            "season" : season,
            "round" : round,
            "day" : day,
            "m" : self.MY_MEMBER_ID,
            "mk" : self.ACCESS_KEY,
            "json" : 1
        }
        
        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")
        
        return datetime.datetime.strptime(data.get("date")[0].get('date'), "%Y-%m-%d").date()
    
    
#----------------------------------------------------------------
# DISPLAY TOOL - Get a human-readable summary of players in a team from the BR API
#----------------------------------------------------------------
class Converter_From_Season_Round_Day_to_Date_INFO(Tool):
    name = "date_converter_from_season_round_day_to_date_info"
    description = (
        "Returns the date (in YYYY-MM-DD) format) of a given Season Round Day as a human-readable string"
    )
    inputs = {
        'season': {'type': 'integer', 'description': 'the season number'},
        'round': {'type': 'integer', 'description': 'the round number'},
        'day': {'type': 'integer', 'description': 'the day number within the round'}
    }
    output_type = "object" # datetime.date

    def __init__(self,
                 season=None,
                 round=None,
                 day=None,
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
        
        self.season = season
        self.round = round
        self.day = day
        self.response = None
        self.filename = ""
        self.BR_API="http://classic-api.blackoutrugby.com"
        
        
    def forward(self, season: int, round: int, day: int) -> datetime.date:
        """
        method to compute the date from season, round, day
        :param season: the season number
        :param round: the round number
        :param day: the day number within the round
        :return: date in YYYY-MM-DD format
        """
        
        payload = {
            "d" : self.DEV_ID,
            "dk" : self.DEV_KEY,
            "r" : "dt",  # date tool
            "season" : season,
            "round" : round,
            "day" : day,
            "m" : self.MY_MEMBER_ID,
            "mk" : self.ACCESS_KEY,
            "json" : 1
        }
        
        r = requests.get(self.BR_API, params=payload)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "Ok":
            raise RuntimeError(f"BR API error: {data.get('status')}")
        
        return data.get("date")
    
    
#----------------------------------------------------------------
#  TESTING THE TOOL
#----------------------------------------------------------------

if __name__ == "__main__":
    mytool = Converter_From_Season_Round_Day_to_Date_INFO()
    r = mytool.forward(season=59, round=13, day=5)
    print(r)  # Example date
    mytool_info = Converter_From_Season_Round_Day_to_Date_DATA()
    info = mytool_info.forward(season=59, round=13, day=5)
    print(info)  # Example date