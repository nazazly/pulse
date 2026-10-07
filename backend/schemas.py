from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class SportType(str, Enum):
    CS2 = "cs2"
    VALORANT = "valorant"
    FOOTBALL = "football"

class MatchStatus(str, Enum):
    UPCOMING = "UPCOMING"
    LIVE = "LIVE"
    FINISHED = "FINISHED"

class TeamBasic(BaseModel):
    id: str
    name: str
    acronym: Optional[str] = None
    logo_url: Optional[str] = None

class NormalisedMatch(BaseModel):
    id: str
    sport: SportType
    tournament_name: str
    home_team: TeamBasic
    away_team: TeamBasic
    home_score: Optional[int] = 0
    away_score: Optional[int] = 0
    status: MatchStatus
    scheduled_at_sgt: str
    winner_team_id: Optional[str] = None