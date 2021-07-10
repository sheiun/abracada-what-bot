from __future__ import annotations

from typing import TYPE_CHECKING, List
from uuid import uuid4

from telegram import InlineQueryResultArticle
from telegram import InlineQueryResultCachedSticker as Sticker
from telegram import InputTextMessageContent

from card import Card, PASS
from constants import INVALID_INPUT_TEXT
from utils import display_name

if TYPE_CHECKING:
    from telegram import InlineQueryResult

    from player import Player

INPUT_INVALID = InputTextMessageContent(INVALID_INPUT_TEXT)


def add_cards(results: List[InlineQueryResult], player: Player):
    if player.game.current_player == player:
        results.append(
            InlineQueryResultArticle(
                uuid4(), title="請選擇你要施展的魔法！", input_message_content=INPUT_INVALID,
            )
        )
        start = int(player.last_played.id) if player.last_played else 1
        for i in range(start, 9):
            card = Card.from_id(str(i))
            results.append(Sticker(card.id, sticker_file_id=card.sticker_id))
        if player.last_played:
            results.append(Sticker("pass", PASS["sticker_id"]))
    if player.secret_cards:
        results.append(
            InlineQueryResultArticle(
                uuid4(), title="你的祕密魔法石", input_message_content=INPUT_INVALID,
            )
        )
        for c in player.secret_cards:
            results.append(
                Sticker(uuid4(), c.sticker_id, input_message_content=INPUT_INVALID)
            )
    game = player.game
    for p in game.players:
        if p == player:
            continue
        results.append(
            InlineQueryResultArticle(
                uuid4(),
                title=display_name(p.user) + " 的魔法石",
                input_message_content=INPUT_INVALID,
            ),
        )
        for c in p.cards:
            results.append(
                Sticker(uuid4(), c.sticker_id, input_message_content=INPUT_INVALID)
            )


def add_no_game(results: List[InlineQueryResult]):
    """Add text result if user is not playing"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title="你沒在玩ㄡ",
            input_message_content=InputTextMessageContent("我錯了我沒加入遊戲不該亂點 😢"),
        )
    )


def add_not_started(results: List[InlineQueryResult]):
    """Add text result if the game has not yet started"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title="還沒開始ㄡ",
            input_message_content=InputTextMessageContent("趕快按開始ㄅ"),
        )
    )
