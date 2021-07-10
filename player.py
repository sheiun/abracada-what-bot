from __future__ import annotations

from logging import getLogger
from random import choice
from typing import List, TYPE_CHECKING, Optional

from card import Card

if TYPE_CHECKING:
    from game import Game


class Player:
    """
    This class represents a player.
    It is basically a circular doubly-linked list.
    On initialization, it will connect itself to a game and its
    other players by placing itself behind the current player.
    """

    prev: Player
    next: Player

    def __init__(self, game, user):
        self.game: Game = game
        self.user = user

        self.cards: List[Card] = []
        self.secret_cards: List[Card] = []
        self.last_played: Optional[Card] = None
        self.hp: int = 6
        self.score: int = 0

        self.logger = getLogger(__name__)

        # Check if this player is the first player in this game.
        if game.current_player:
            self.next = game.current_player
            self.prev = game.current_player.prev
            game.current_player.prev.next = self
            game.current_player.prev = self
        else:
            self.next = self
            self.prev = self
            game.current_player = self

    @property
    def left(self) -> Player:
        return self.prev

    @property
    def right(self) -> Player:
        return self.next

    def leave(self):
        """Removes player from the game and closes the gap in the list"""
        if self.next is self:
            return

        self.next.prev = self.prev
        self.prev.next = self.next
        self.next = None
        self.prev = None

        self.cards = []
        self.discard_amount = 0

    def __repr__(self):
        return repr(self.user)

    def __str__(self):
        return str(self.user)

    def draw(self):
        while len(self.cards) < 5:
            self.cards.append(self.game.deck.draw())

    def has(self, card: Card):
        return card in self.cards

    def play(self, card: Card) -> int:
        """Plays a card and removes it from hand"""
        indices = [i for i, c in enumerate(self.cards) if c == card]
        index = choice(indices)
        self.cards.pop(index)
        self.game.used_cards[card.id] += 1
        self.last_played = card
        return index
