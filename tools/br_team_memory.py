# br_team_memory_tools.py

# --------------------------------------------------------------------
#
#  TOOLS FOR TEAM MEMORY MANAGEMENT IN BLACKOUT RUGBY AGENT
#
# --------------------------------------------------------------------
# br_team_memory_tools.py

import os
import json
from smolagents import Tool
from typing import Optional

SNAPSHOT_DIR = "./memory/team_snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

class SaveTeamSnapshot(Tool):
    name = "save_team_snapshot"
    description = (
        "Analytical tool: saves the latest snapshot of a team's player data to disk. "
        "This allows tracking changes over time, including all player stats and skills."
    )
    inputs = {
        "team_id": {"type": "integer", "description": "The ID of the team to save snapshot for"},
        "players_data": {"type": "object", "description": "List of dictionaries representing full player data"}
    }
    output_type = "boolean"

    def forward(self, team_id: int, players_data: list[dict]) -> bool:
        filename = os.path.join(SNAPSHOT_DIR, f"team_{team_id}.json")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(players_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving snapshot for team {team_id}: {e}")
            return False


class LoadTeamSnapshot(Tool):
    name = "load_team_snapshot"
    description = (
        "Analytical tool: loads the last saved snapshot of a team's player data from disk. "
        "Returns None if no snapshot exists."
    )
    inputs = {
        "team_id": {"type": "integer", "description": "The ID of the team to load snapshot for"}
    }
    output_type = "object"

    def forward(self, team_id: int) -> Optional[list[dict]]:
        filename = os.path.join(SNAPSHOT_DIR, f"team_{team_id}.json")
        if not os.path.exists(filename):
            return None
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)


class CompareTeamSnapshots(Tool):
    name = "compare_team_snapshots"
    description = (
        "Analytical tool: compares a new snapshot of a team's player data with the previous snapshot. "
        "Returns a dictionary summarizing changes in all player characteristics, including skills. "
        "Returns None if no previous snapshot exists."
    )
    inputs = {
        "team_id": {"type": "integer", "description": "The ID of the team"},
        "new_snapshot": {"type": "object", "description": "List of dictionaries representing current full player data"}
    }
    output_type = "object"

    def forward(self, team_id: int, new_snapshot: list[dict]) -> Optional[dict]:
        old_snapshot = LoadTeamSnapshot().forward(team_id)
        if old_snapshot is None:
            return None

        changes = {
            "new_players": [],
            "removed_players": [],
            "attribute_changes": {}
        }

        old_players_by_name = {p["name"]: p for p in old_snapshot}
        new_players_by_name = {p["name"]: p for p in new_snapshot}

        # New and removed players
        for name in new_players_by_name:
            if name not in old_players_by_name:
                changes["new_players"].append(name)
        for name in old_players_by_name:
            if name not in new_players_by_name:
                changes["removed_players"].append(name)

        # Attribute changes
        for name in new_players_by_name:
            if name in old_players_by_name:
                old_p = old_players_by_name[name]
                new_p = new_players_by_name[name]
                diff = {}

                # Check top-level attributes
                for attr in ["age", "salary", "form", "aggression", "discipline",
                             "leadership", "experience", "weight", "height", "csr", "energy"]:
                    if old_p.get(attr) != new_p.get(attr):
                        diff[attr] = {"old": old_p.get(attr), "new": new_p.get(attr)}

                # Check skills
                for skill in old_p.get("skills", {}):
                    if old_p["skills"].get(skill) != new_p["skills"].get(skill):
                        diff[skill] = {"old": old_p["skills"].get(skill), "new": new_p["skills"].get(skill)}

                if diff:
                    changes["attribute_changes"][name] = diff

        return changes


class ReportTeamChanges(Tool):
    name = "report_team_changes"
    description = (
        "Analytical tool: converts the output of CompareTeamSnapshots into a readable text report. "
        "Summarizes all changes in player roster and attributes."
    )
    inputs = {
        "changes": {"type": "object", "description": "The dictionary output from CompareTeamSnapshots"}
    }
    output_type = "string"

    def forward(self, changes: dict) -> str | None:
        if changes is None:
            return "No previous snapshot exists. Unable to report changes."

        lines = []

        # New players
        new_players = changes.get("new_players", [])
        lines.append("New players added:" if new_players else "No new players added.")
        for name in new_players:
            lines.append(f" - {name}")

        # Removed players
        removed_players = changes.get("removed_players", [])
        lines.append("Players removed:" if removed_players else "No players removed.")
        for name in removed_players:
            lines.append(f" - {name}")

        # Attribute changes
        attribute_changes = changes.get("attribute_changes", {})
        if attribute_changes:
            lines.append("Changes in player attributes:")
            for name, attrs in attribute_changes.items():
                lines.append(f" - {name}:")
                for attr, vals in attrs.items():
                    lines.append(f"     {attr}: {vals['old']} → {vals['new']}")
        else:
            lines.append("No changes in player attributes detected.")

        return "\n".join(lines)
