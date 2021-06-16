from dotenv import load_dotenv
import os
import logging
import utils

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from validators import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

FIRST, SECOND, THIRD, FOURTH = range(4)

# TP - track_price
# TE - track existence
# SI - show_items
# DEL - delete_item
# START - start_over
TP, TE, SI, DEL, START = range(5)


def get_base_inline_keyboard():
    """ Получаем базовую клавиатуру для главного меню. """
    keyboard = [
        [InlineKeyboardButton("Отслеживание снижения цены", callback_data=str(TP))],
        [InlineKeyboardButton("Появление товара", callback_data=str(TE))],
        [InlineKeyboardButton("Мой список", callback_data=str(SI))],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_keyboard_cancel():
    """ Получаем клавиатуру перехода в главное меню. """
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=str(START))]]
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    update.message.reply_text(
        text="Выберите действие:",
        reply_markup=get_base_inline_keyboard(),
    )
    return FIRST


def start_over(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="Выберите действие:",
        reply_markup=get_base_inline_keyboard()
    )
    return FIRST


def track_price(update, context):
    """ Отслеживаем снижение цены. """
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="Введите артикул",
    )
    return SECOND


def ask_size_tp(update, context):
    """ Проверяем товар по артикулу и наличие размеров. """
    # проверяем артикул
    article = validate_article(article=update.message.text)
    if article is None:
        update.message.reply_text(
            text="Пожалуйста введите корректный артикул или нажмите 'Отмена'",
            reply_markup=get_keyboard_cancel(),
        )
        return SECOND
    # проверяем, что товар в продаже
    item_price = validate_item_price(article)
    if item_price is None:
        keyboard = [
            [
                InlineKeyboardButton("Отследить", callback_data=str(TE)),
                InlineKeyboardButton("В начало", callback_data=str(START)),
            ],
        ]
        update.message.reply_text(
            text="Нет в продаже. Отслеживать появление?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SECOND
    context.user_data[1] = item_price
    # проверяем существуют ли у товара размеры
    sizes = parser.get_sizes(article)
    if sizes:
        context.user_data[2] = sizes
        update.message.reply_text("Укажите размер")
        return THIRD
    update.message.reply_text("Введите цену")
    return FOURTH


def ask_price_tp(update, context):
    """ Сверяем размер товара с размером, переданным пользователем. """
    size_value = update.message.text
    size = utils.get_size_from_user(size_value)
    sizes = context.user_data[2]
    if size not in sizes:
        update.message.reply_text(
            text="Пожалуйста введите корректный размер или нажмите 'Отмена'",
            reply_markup=get_keyboard_cancel()
        )
        return THIRD
    # если этого размера нет
    if not sizes[size]:
        keyboard = [[InlineKeyboardButton("Главное меню", callback_data=str(START))]]
        update.message.reply_text(
            text="Сейчас этого размера нет. "
                 "Можете отследить появление через"
                 " главное меню или выбрать другой размер",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return THIRD
    update.message.reply_text("Введите цену")
    return FOURTH


def get_info_tp(update, context):
    """ Проверяем цену, запрошенную пользователем.
        Собираем воедино полученные данные, сохраняем в БД.
    """
    # получить цену
    # проверить полученные данные
    price = update.message.text
    item_price = context.user_data[1]
    correct_price = validate_price(item_price, price)
    if not correct_price:
        update.message.reply_text(
            text="Пожалуйста введите корректную цену или нажмите 'Отмена'",
            reply_markup=get_keyboard_cancel(),
        )
        return FOURTH
    # TODO здесь нужно сохранить в БД
    update.message.reply_text(
        text="Товар добавлен в ваш список",
        reply_markup=get_base_inline_keyboard(),
    )
    return FIRST


def track_existence(update, context):
    """ Отслеживаем наличие товара. """
    pass


def show_items(update, context):
    """ Смотрим свой список товаров. """
    pass


def delete_item(update, context):
    """ Удаляем товар из БД. """
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
                CallbackQueryHandler(delete_item, pattern='^' + str(DEL) + '$'),
            ],
            SECOND: [
                MessageHandler(Filters.text, ask_size_tp, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            THIRD: [
                MessageHandler(Filters.text, ask_price_tp, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            FOURTH: [
                MessageHandler(Filters.text, get_info_tp, pass_chat_data=True),
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
