from dotenv import load_dotenv
import os

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler

FIRST = range(1)

# TP - track_price
# TE - track existence
# SI - show_items
# START - start_over
TP, TE, SI, START = range(4)


def get_base_inline_keyboard():
    """ Получаем базовую клавиатуру для
        главного меню
    """
    keyboard = [
        [InlineKeyboardButton("Отслеживание снижения цены", callback_data=str(TP))],
        [InlineKeyboardButton("Появление товара", callback_data=str(TE))],
        [InlineKeyboardButton("Мой список", callback_data=str(SI))],
    ]
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    update.message.reply_text(
        text="Выберите действие:",
        reply_markup=get_base_inline_keyboard(),
    )
    return FIRST


def start_over(update, context):
    print('start_over')
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="Выберите действие:",
        reply_markup=get_base_inline_keyboard()
    )
    return FIRST


def track_price(update, context):
    """ Отслеживаем снижение цены """
    pass


def track_existence(update, context):
    """ Отслеживаем наличие товара """
    pass


def show_items(update, context):
    """ Смотрим свой список товаров """
    pass


def main():
    load_dotenv()
    updater = Updater(token=os.getenv("TG_TOKEN"))
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [
                CallbackQueryHandler(track_price, pattern='^' + str(TP) + '$'),
                CallbackQueryHandler(track_existence, pattern='^' + str(TE) + '$'),
                CallbackQueryHandler(show_items, pattern='^' + str(SI) + '$'),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
