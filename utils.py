from card import Card

HEADER = "－－－《{text}》－－－\n"


def display_name(user):
    """ Get the current players name including their username, if possible """
    user_name = user.first_name
    if user.username:
        user_name += "（@" + user.username + "）"
    return user_name


def make_round_settlement(game) -> str:
    text = HEADER.format(text="血量")
    for p in game.players:
        text += display_name(p.user) + f"（{p.hp}）\n"
    return text


def make_current_settlement(game) -> str:
    text = HEADER.format(text="分數")
    for p in game.players:
        text += display_name(p.user) + f"（{p.score} 分）\n"
    return text.rstrip()


def make_settlement(game) -> str:
    text = HEADER.format(text="結束")
    players = game.players
    highest, lowest = float("-inf"), 0
    for p in players:
        if p.score > highest:
            highest = p.score
        if p.score < lowest:
            lowest = p.score

    for p in players:
        # prepend emoji to player
        if p.score == highest:
            text += "🏆 "
        elif p.score == lowest:
            text += "👎 "
        else:
            text += "👍 "
        text += f"{display_name(p.user)}（{p.score} 分）\n"
    return text.rstrip()


def make_game_start(game) -> str:
    text = HEADER.format(text="開始")
    text += display_name(game.current_player.user) + f"請選擇你要施展的魔法！"
    return text


def make_room_info(game) -> str:
    text = HEADER.format(text="房間")
    others = [p.user for p in game.players]
    others.remove(game.starter)
    text += f"房主：{display_name(game.starter)}\n"
    for u in others:
        text += display_name(u) + "\n"
    return text.rstrip()


def make_used_cards(game) -> str:
    text = HEADER.format(text="場上")
    text += f"剩餘 {len(game.deck.cards)} 個魔法石！\n"
    for i in range(1, 9):
        text += str(Card.from_id(str(i))) + "\n"
        used = game.used_cards[str(i)]
        text += f"{'◼' * used}{(i-used) * '◻'}\n"
    return text
