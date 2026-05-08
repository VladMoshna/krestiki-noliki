import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

games = {}  # chat_id -> game state


def empty_board():
    return [" "] * 9


def create_board_markup(board):
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []

    for i in range(9):
        text = board[i] if board[i] != " " else "⬜"
        buttons.append(
            InlineKeyboardButton(text, callback_data=f"move_{i}")
        )

    markup.add(*buttons)
    return markup


def check_winner(board, symbol):
    wins = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    return any(all(board[i] == symbol for i in combo) for combo in wins)


def bot_move(board, bot_symbol):
    free = [i for i, v in enumerate(board) if v == " "]
    if free:
        return random.choice(free)
    return None


@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Грати за ❌", callback_data="choose_X"),
        InlineKeyboardButton("Грати за ⭕", callback_data="choose_O"),
    )
    bot.send_message(message.chat.id, "Обери, чим будеш ходити:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id

    if call.data.startswith("choose_"):
        user_symbol = call.data[-1]
        bot_symbol = "O" if user_symbol == "X" else "X"

        games[chat_id] = {
            "board": empty_board(),
            "user": user_symbol,
            "bot": bot_symbol,
            "turn": "user" if user_symbol == "X" else "bot"
        }

        board = games[chat_id]["board"]

        bot.edit_message_text(
            "Гра почалась!",
            chat_id,
            call.message.message_id,
            reply_markup=create_board_markup(board)
        )

        if games[chat_id]["turn"] == "bot":
            make_bot_turn(chat_id, call.message.message_id)

    elif call.data.startswith("move_"):
        if chat_id not in games:
            return

        game = games[chat_id]
        if game["turn"] != "user":
            return

        idx = int(call.data.split("_")[1])
        board = game["board"]

        if board[idx] != " ":
            return

        board[idx] = game["user"]

        if check_winner(board, game["user"]):
            end_game(call, "Ти переміг")
            return

        if " " not in board:
            end_game(call, "Нічия")
            return

        game["turn"] = "bot"
        make_bot_turn(chat_id, call.message.message_id)


def make_bot_turn(chat_id, message_id):
    game = games[chat_id]
    board = game["board"]

    idx = bot_move(board, game["bot"])
    if idx is not None:
        board[idx] = game["bot"]

    if check_winner(board, game["bot"]):
        bot.edit_message_text(
            "Бот переміг",
            chat_id,
            message_id,
            reply_markup=create_board_markup(board)
        )
        del games[chat_id]
        return

    if " " not in board:
        bot.edit_message_text(
            "Нічия",
            chat_id,
            message_id,
            reply_markup=create_board_markup(board)
        )
        del games[chat_id]
        return

    game["turn"] = "user"
    bot.edit_message_text(
        "Твій хід:",
        chat_id,
        message_id,
        reply_markup=create_board_markup(board)
    )


def end_game(call, text):
    chat_id = call.message.chat.id
    game = games[chat_id]

    bot.edit_message_text(
        text,
        chat_id,
        call.message.message_id,
        reply_markup=create_board_markup(game["board"])
    )

    del games[chat_id]


print("Bot is running...")
bot.infinity_polling()