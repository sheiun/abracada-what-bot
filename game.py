from __future__ import annotations

from enum import IntEnum
from logging import getLogger
from typing import TYPE_CHECKING, List, Optional

from card import CARDS
from config import OPEN_LOBBY
from deck import Deck
from errors import DeckEmptyError, NotEnoughPlayersError

if TYPE_CHECKING:
    from telegram import User

    from player import Player


class Game:
    class State(IntEnum):
        """The state represents current state"""

        START = 0
        PLAYING = 1
        END = 2

    current_player: Optional[User] = None
    starter: Optional[User] = None
    state: Game.State = State.START
    open = OPEN_LOBBY

    def __init__(self, chat):
        self.chat = chat

        self.deck = Deck()
        self.used_cards = {str(k): 0 for k in range(1, 9)}
        self.secret_cards = []

        self.logger = getLogger(__name__)

    @property
    def started(self) -> bool:
        return self.state > Game.State.START

    @property
    def ended(self) -> bool:
        return self.state == Game.State.END

    def start(self):
        self.deck.init(CARDS.copy())
        p_amount = len(self.players)
        self.used_cards = {str(k): 0 for k in range(1, 9)}
        if 2 <= p_amount <= 3:
            discard_amount = 6 * (4 - p_amount)
            for i in range(discard_amount):
                self.used_cards[self.deck.cards[i].id] += 1
            self.deck.cards = self.deck.cards[discard_amount:]
        self.secret_cards = self.deck.cards[:4]
        self.deck.cards = self.deck.cards[4:]

        self.state = Game.State.PLAYING
        self.logger.info(f"{self.state} == {self.State.PLAYING}")

        for player in self.players:
            player.hp = 6
            player.last_played = None
            player.secret_cards = []
            player.cards = []
            player.draw()

    def turn(self):
        if self.current_player is None:
            raise NotEnoughPlayersError()
        self.current_player.last_played = None
        try:
            self.current_player.draw()
        except DeckEmptyError:
            pass
        self.current_player = self.current_player.next

    @property
    def players(self) -> List[Player]:
        if not self.current_player:
            return []

        players = []
        current_player = self.current_player
        itplayer = current_player.next
        players.append(current_player)
        while itplayer and itplayer is not current_player:
            players.append(itplayer)
            itplayer = itplayer.next
        return players

    def has_end(self):
        if not self.current_player:
            raise Exception("No current player")
        if not self.current_player.cards:
            return True
        if not self.deck.cards:
            return True
        for player in self.players:
            if player.hp == 0:
                return True
        return False

    def scoring(self):
        """Called after has_end """
        assert self.has_end()
        if not self.current_player:
            raise Exception("No current player")
        # Case 1
        if not self.current_player.cards:
            self.current_player.score += 3
        # Case 2
        elif self.current_player.hp > 0:
            self.current_player.score += 3

            for p in self.players:
                if p.hp != 0 and p != self.current_player:
                    p.score += 1
        # Case 3
        elif self.current_player.hp == 0:
            for p in self.players:
                if p.hp != 0:
                    p.score += 1
        # Bonus (Owls)
        for p in self.players:
            if p.hp != 0:
                p.score += len(p.secret_cards)

        for p in self.players:
            if p.score > 8:
                p.score = 8

    def has_winner(self) -> bool:
        for p in self.players:
            if p.score == 8:
                return True
        return False
