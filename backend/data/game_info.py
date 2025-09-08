from dataclasses import dataclass
from dataclasses import field
from enum import Enum

class GameState(str, Enum):
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
    current_state: GameState = GameState.LOBBY

    def answers_submitted(self) -> bool:
        return all(player.answer_submitted for player in self.players.values())

    def votes_submitted(self) -> bool:
        return all(player.vote_submitted for player in self.players.values())

    def next_state(self, host_override=False) -> GameState:
        """
        Move to the next state if conditions are met.
        """
        if self.current_state == GameState.LOBBY:
                self.current_state = GameState.QUESTION
        
        elif self.current_state == GameState.QUESTION:
            if self.answers_submitted():
                self.current_state = GameState.VOTING
        
        elif self.current_state == GameState.VOTING:
             if self.votes_submitted():
                self.current_state = GameState.RESULTS

        elif self.current_state == GameState.RESULTS:
            self.new_round()
            self.current_state = GameState.LOBBY

        return self.current_state
    
    def new_round(self):
        """Reset per-round values for a new round."""
        for player in self.players.values():
            player.is_imposter = False
            player.answer_submitted = False
            player.vote_submitted = False

@dataclass
class Player:
    id: str
    name: str
    is_imposter: bool 
    sid: str
    answer_submitted: bool = False
    vote_submitted: bool = False
