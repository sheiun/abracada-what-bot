import logging
from typing import TYPE_CHECKING, Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    Filters,
    InlineQueryHandler,
    MessageHandler,
    Updater,
)
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from card import Card
from config import MIN_PLAYERS, TOKEN, WORKERS
from constants import INVALID_INPUT_TEXT
from errors import (
    AlreadyJoinedError,
    DeckEmptyError,
    GameStartedException,
    LobbyClosedError,
    NoGameInChatError,
    NotEnoughPlayersError,
)
from game_manager import GameManager
from results import add_cards, add_no_game, add_not_started
from utils import (
    display_name,
    make_current_settlement,
    make_game_start,
    make_room_info,
    make_round_settlement,
    make_settlement,
    make_used_cards,
)

if TYPE_CHECKING:
    from telegram.message import Message


logging.basicConfig(
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Room:
    def __init__(self, updater: Updater):
        self.updater = updater
        self.handlers = [
            InlineQueryHandler(self.reply_query, run_async=True),
            ChosenInlineResultHandler(self.process_result, run_async=True),
            CallbackQueryHandler(self.reply_callback, run_async=True),
            MessageHandler(
                Filters.via_bot(self.updater.bot.id),
                self.delete_invalid,
                run_async=True,
            ),
            CommandHandler("new", self.new, run_async=True),
            CommandHandler("kill", self.kill, run_async=True),
            CommandHandler("join", self.join, run_async=True),
            CommandHandler("leave", self.leave, run_async=True),
            CommandHandler("start", self.start, run_async=True),
            CommandHandler("info", self.info, run_async=True),
            MessageHandler(
                Filters.status_update.left_chat_member, self.leave_group, run_async=True
            ),
        ]
        self.register()

    def register(self):
        for handler in self.handlers:
            self.updater.dispatcher.add_handler(handler)
        self.updater.dispatcher.add_error_handler(self.error)

    def info(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if games:
            game = games[-1]
            if game.ended:
                update.message.reply_text("遊戲已結束！")
            else:
                update.message.reply_text(make_room_info(game))
        else:
            update.message.reply_text("目前沒有房間！請用 /new 開房！")

    def new(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if games:
            game = games[-1]
            if game.started and len(game.players) >= MIN_PLAYERS:
                text = "已經開始ㄌ 下次請早ㄡ"
            else:
                text = "房間早就開ㄌ，用 /info 查看資訊，用 /join 加入"
            update.message.reply_text(text)
            return

        game = gm.new_game(update.message.chat)
        game.starter = update.message.from_user
        update.message.reply_text("幫你開ㄌ，其他人可以用 /join 加入")
        # NOTE: auto join
        self.join(update, context)

    def kill(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if not games:
            return

        user = update.message.from_user
        if user.username == "sheiun":
            try:
                gm.end_game(chat, user)
                text = "遊戲終了！"
            except NoGameInChatError:
                return
        else:
            text = "你沒有權限"
        update.message.reply_text(text)

    def join(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        try:
            gm.join_game(update.message.from_user, chat)
        except LobbyClosedError:
            text = "關房了"
        except NoGameInChatError:
            text = "沒房ㄌ"
        except AlreadyJoinedError:
            text = "已經加入ㄌ拉"
        except DeckEmptyError:
            text = "牌不夠ㄌ"
        except GameStartedException:
            text = "已經開始ㄌ"
        else:
            text = "加入成功ㄌ"
        update.message.reply_text(text)

    def leave(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        user = update.message.from_user

        player = gm.player_for_user_in_chat(user, chat)
        if player is None:
            text = "你不在遊戲內ㄡ"
        else:
            game = player.game
            try:
                gm.leave_game(user, chat)
            except NoGameInChatError:
                text = "你不在遊戲內ㄡ"
            except NotEnoughPlayersError:
                text = "遊戲結束ㄌ"
            else:
                if game.started:
                    text = f"好ㄉ。下位玩家 {display_name(game.current_player.user)}"
                else:
                    text = f"{display_name(user)} 離開ㄌ"
        update.message.reply_text(text)

    def start(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return
        text = ""
        markup = None
        try:
            game = gm.chatid_games[chat.id][-1]
        except (KeyError, IndexError):
            text = "還沒開房ㄡ"
        else:
            if game.started:
                text = "已經開始ㄌㄡ"
            elif len(game.players) < MIN_PLAYERS:
                text = f"至少要 {MIN_PLAYERS} 人才能開ㄡ"
            else:
                game.start()
                text = make_game_start(game)
                markup = choices
                context.bot.send_message(chat.id, text=make_room_info(game))
                context.bot.send_message(chat.id, text=make_used_cards(game))
        update.message.reply_text(text, reply_markup=markup)

    def leave_group(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        user = update.message.left_chat_member
        try:
            gm.leave_game(user, chat)
        except NoGameInChatError:
            return
        except NotEnoughPlayersError:
            gm.end_game(chat, user)
            text = "遊戲終了！"
        else:
            text = display_name(user) + " 被踢出遊戲ㄌ"
        context.bot.send_message(chat.id, text=text)

    def reply_query(self, update: Update, context: CallbackContext):
        results = []

        user = update.inline_query.from_user
        try:
            player = gm.userid_current[user.id]
        except KeyError:
            add_no_game(results)
        else:
            if not player.game.started:
                add_not_started(results)
            else:
                add_cards(results, player)
        update.inline_query.answer(results, cache_time=0)

    def process_result(self, update: Update, context: CallbackContext):
        user = update.chosen_inline_result.from_user
        result_id = update.chosen_inline_result.result_id
        try:
            player = gm.userid_current[user.id]
            game = player.game
            chat = game.chat
        except (KeyError, AttributeError):
            return
        if result_id in ("hand", "gameinfo", "nogame"):
            return
        if len(result_id) == 36:
            return
        reply: Callable[[str], Message] = lambda text: context.bot.send_message(
            chat.id, text=text, reply_to_message_id=message_id
        )
        if player != game.current_player:
            reply(display_name(user) + " 還沒輪到你！")
            return
        if result_id.isdigit() and 1 <= int(result_id) <= 8:
            message_id = update.chosen_inline_result.inline_message_id
            card = Card.from_id(result_id)
            if player.last_played and player.last_played > card:
                reply(display_name(user) + " 你只能施展更強大的魔法！")
                return
            if player.has(card):
                idx = player.play(card)
                message_succ = reply(
                    f"施展成功！第 {idx+1} 個魔法石被移除！\n你還有 {len(player.cards)} 個魔法石！"
                )
                # NOTE: do card effect
                if card == 1:
                    message = message_succ.reply_dice()
                    dice = message.dice
                    value = 3 if dice.value % 3 == 0 else dice.value % 3
                    message.reply_text(f"你骰出了 {dice.value} 所有人扣 {value} 點血！")
                    for p in game.players:
                        if p != game.current_player:
                            p.hp -= value
                elif card == 2:
                    player.hp += 1
                elif card == 3:
                    message = message_succ.reply_dice()
                    dice = message.dice
                    value = 3 if dice.value % 3 == 0 else dice.value % 3
                    message.reply_text(f"你骰出了 {dice.value} 回復 {value} 點血！")
                    player.hp += value
                elif card == 4:
                    s_card = game.secret_cards.pop(0)
                    player.secret_cards.append(s_card)
                elif card == 5:
                    if player.left != player.right:
                        player.right.hp -= 1
                    player.left.hp -= 1
                elif card == 6:
                    player.left.hp -= 1
                elif card == 7:
                    player.right.hp -= 1
                elif card == 8:
                    player.hp += 1

                for p in game.players:
                    if p.hp > 6:
                        p.hp = 6
                    elif p.hp < 0:
                        p.hp = 0
            else:
                message_fail = reply(f"施展失敗！你沒有 {card}！")
                if card == 1:
                    message = message_fail.reply_dice()
                    dice = message.dice
                    value = 3 if dice.value % 3 == 0 else dice.value % 3
                    message.reply_text(f"骰出了 {dice.value} 你扣了 {value} 點血！")

                    player.hp -= value
                    if player.hp < 0:
                        player.hp = 0
                else:
                    player.hp -= 1

                if player.hp != 0:
                    game.turn()
                    message_fail.reply_text(f"你剩下 {player.hp} 點血！")
                else:
                    message_fail.reply_text("魔法師死亡！")
            context.bot.send_message(chat.id, text=make_round_settlement(game))

            if game.has_end():
                game.scoring()

                if not game.has_winner():
                    context.bot.send_message(
                        chat.id, text=make_current_settlement(game)
                    )
                    game.start()
                else:
                    gm.end_game(chat, user)
                    context.bot.send_message(chat.id, text=make_settlement(game))
                    return
            context.bot.send_message(chat.id, text=make_used_cards(game))
            context.bot.send_message(
                chat.id, text=make_game_start(game), reply_markup=choices,
            )
        elif result_id == "pass":
            if len(player.cards) == 5:
                reply("還沒施展過魔法無法跳過！")
                return
            else:
                draw_amount = min(5 - len(player.cards), len(game.deck.cards))
                game.turn()
                context.bot.send_message(
                    chat.id,
                    text=f"補 {draw_amount} 個魔法石\n剩餘 {len(game.deck.cards)} 個魔法石\n換下一位魔法師 "
                    + display_name(game.current_player.user),
                    reply_markup=choices,
                )
        else:
            logger.info(f"Result: {result_id} is run into else clause!")
            # The card cannot be played

    def reply_callback(self, update: Update, context: CallbackContext):
        return

    def delete_invalid(self, update: Update, context: CallbackContext):
        if update.message.text == INVALID_INPUT_TEXT:
            update.message.delete()

    def error(self, update: Update, context: CallbackContext):
        """Simple error handler"""
        raise context.error

    def launch(self):
        self.updater.start_polling()
        self.updater.idle()


choices = InlineKeyboardMarkup(
    [[InlineKeyboardButton("選牌！", switch_inline_query_current_chat="")]]
)


gm = GameManager()

Room(Updater(token=TOKEN, workers=WORKERS)).launch()
