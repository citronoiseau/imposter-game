from dataclasses import dataclass
from dataclasses import field
from enum import Enum

class GameState(str, Enum):
    SETUP = "SETUP"
    LOBBY = "LOBBY"
    QUESTION = "QUESTION"
    VOTING = "VOTING"
    RESULTS = "RESULTS"

@dataclass
class GameInfo:
    id: str
    players: dict[str, Player] = field(default_factory=dict)
    imposters: int
    inn_question: str
    imp_question: str

@dataclass
class Player:
    id: str
    name: str
    is_imposter: bool 
    sid: str
