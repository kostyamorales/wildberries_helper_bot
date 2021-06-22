from dotenv import load_dotenv
import os
import logging
import utils
import sqlite3
from logs_handler import MyLogsHandler

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode

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

FIRST, TP2, TP3, TP4, TE2, TE3, DEL2 = range(7)
# TP - track_price
# TE - track existence
# SI - show_items
# DEL - delete_item
# START - start_over
TP, TE, SI, DEL, START = range(5)

__connection = None


def get_connection():
    global __connection
    if __connection is None:
        __connection = sqlite3.connect("wb_bot.db", check_same_thread=False)
    return __connection


def init_db(force: bool = False):
    """ Проверяем что нужные таблицы существуют, иначе создаём их
        :param force: явно пересоздать все таблицы
    """
    conn = get_connection()
    conn.execute("PRAGMA foreign_key=on")
    c = conn.cursor()
    if force:
        c.execute("DROP TABLE IF EXISTS wb_bot")

    c.execute("""
        CREATE TABLE IF NOT EXISTS item(
            id          INTEGER PRIMARY KEY,
            profile     INTEGER NOT NULL,
            article     INTEGER NOT NULL,
            item_size   TEXT,
            item_name   TEXT,
            url         TEXT NOT NULL,
            existence   INTEGER,
            user_price  INTEGER,
            FOREIGN KEY (profile) REFERENCES user(external_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user(
        id              INTEGER PRIMARY KEY,
        external_id     INTEGER NOT NULL,
        user_name       TEXT,
        CONSTRAINT chat_id_unique UNIQUE (external_id)
        )
    """)

    conn.commit()


def get_user_record(external_id):
    """ Получаем user если он существует """
    conn = get_connection()
    c = conn.cursor()
    try:
        return c.execute("""
        SELECT external_id
        FROM user
        WHERE external_id == ?
        """, (external_id,)).fetchall()
    except sqlite3.OperationalError:
        return


def add_user_record(external_id, user_name):
    """ Делаем запись в user в БД """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO user (external_id, user_name)
    VALUES (?, ?)
    """, (external_id, user_name))
    conn.commit()


def add_item_record(profile, article, item_size, item_name, url, existence, user_price):
    """ Делаем запись в item в БД """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO item (profile, article, item_size, item_name, url, existence, user_price)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (profile, article, item_size, item_name, url, existence, user_price))
    conn.commit()


def get_items(external_id):
    """ По external_id достаём все товары пользователя """
    conn = get_connection()
    c = conn.cursor()
    try:
        return c.execute("""
        SELECT id, article, item_size, item_name, url, existence, user_price
        FROM item
        WHERE profile == ?
        """, (external_id,)).fetchall()
    except sqlite3.OperationalError:
        return


def get_items_id(external_id):
    """ Получаем id всех товаров из списка пользователя"""
    conn = get_connection()
    c = conn.cursor()
    try:
        return c.execute("""
        SELECT id
        FROM item
        WHERE profile == ?
        """, (external_id,)).fetchall()
    except sqlite3.OperationalError:
        return


def delete_entry(record_id):
    """ Удаляем запись из БД """
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM item WHERE id == ?", (record_id,))
    conn.commit()


def get_price_tracking_goods():
    """ Из БД достаём товары с отслеживаемой ценой """
    conn = get_connection()
    c = conn.cursor()
    try:
        return c.execute("""
        SELECT id, profile, article, item_size, item_name, url, user_price
        FROM item
        WHERE existence == ?
        """, (True, )).fetchall()
    except sqlite3.OperationalError:
        return


def get_tracking_goods():
    """ Из БД достаём товары которые в листе ожидания """
    conn = get_connection()
    c = conn.cursor()
    try:
        return c.execute("""
        SELECT id, profile, article, item_size, item_name, url, user_price
        FROM item
        WHERE existence == ?
        """, (False, )).fetchall()
    except sqlite3.OperationalError:
        return


def get_base_inline_keyboard():
    """ Получаем базовую клавиатуру для главного меню. """
    keyboard = [
        [InlineKeyboardButton("Отслеживание снижения цены", callback_data=str(TP))],
        [InlineKeyboardButton("Появление товара", callback_data=str(TE))],
        [InlineKeyboardButton("Мой список", callback_data=str(SI))],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_keyboard_cancel(button_name):
    """ Получаем клавиатуру перехода в главное меню. """
    keyboard = [[InlineKeyboardButton(button_name, callback_data=str(START))]]
    return InlineKeyboardMarkup(keyboard)


def get_keyboard_delete_in_show_items():
    """ Получаем клавиатуру перехода в главное меню с кнопкой удалить. """
    keyboard = [
        [InlineKeyboardButton("Удалить", callback_data=str(DEL))],
        [InlineKeyboardButton("Главное меню", callback_data=str(START))],
    ]
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    update.message.reply_text(
        text="*Выберите действие:*",
        reply_markup=get_base_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def start_over(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="*Выберите действие:*",
        reply_markup=get_base_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def track_price(update, context):
    """ Отслеживаем снижение цены. """
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="*Введите артикул*",
        parse_mode=ParseMode.MARKDOWN,
    )
    return TP2


def ask_size_tp(update, context):
    """ Проверяем товар по артикулу и наличие размеров. """
    # проверяем артикул
    article = validate_article(update.message.text)
    if article is None:
        update.message.reply_text(
            text='Пожалуйста введите корректный артикул или нажмите *"Отмена"*',
            reply_markup=get_keyboard_cancel("Отмена"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP2
    context.user_data[1] = article
    # проверяем, что товар в продаже
    item_price = validate_item_price(article)
    if item_price is None:
        update.message.reply_text(
            text='Товара нет в продаже. Пожалуйста введите корректный артикул или '
                 'можете отследить появление этого товара через *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP2
    context.user_data[2] = item_price
    # проверяем существуют ли у товара размеры
    sizes = parser.get_sizes(article)
    if sizes:
        context.user_data[3] = sizes
        update.message.reply_text(
            text="*Укажите размер*",
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP3
    size = 0
    context.user_data[4] = size
    update.message.reply_text(
        text="*Введите цену*",
        parse_mode=ParseMode.MARKDOWN,
    )
    return TP4


def ask_price_tp(update, context):
    """ Сверяем размер товара с размером, переданным пользователем.
        Спрашиваем цену, при достижении которой оповещать.
    """
    sizes = context.user_data[3]
    size = validate_size(update.message.text, sizes)
    # если введенное значение не корректно
    if size is None:
        update.message.reply_text(
            text='Пожалуйста введите корректный размер или нажмите *"Отмена"*',
            reply_markup=get_keyboard_cancel("Отмена"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP3
    # если этого размера нет
    if not sizes[size]:
        update.message.reply_text(
            text='Размера нет в продаже. Пожалуйста введите корректный размер или '
                 'можете отследить появление данного размера через *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP3
    context.user_data[4] = size
    update.message.reply_text(
        text="*Введите цену*",
        parse_mode=ParseMode.MARKDOWN,
    )
    return TP4


def get_info_tp(update, context):
    """ Проверяем цену, запрошенную пользователем.
        Собираем воедино полученные данные, сохраняем в БД.
    """
    # получить цену
    # проверить полученные данные
    price = update.message.text
    item_price = context.user_data[2]
    correct_price = validate_price(item_price, price)
    if not correct_price:
        update.message.reply_text(
            text='Пожалуйста введите корректную цену или нажмите *"Отмена"*',
            reply_markup=get_keyboard_cancel("Отмена"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TP4
    # сохраняем в БД
    article = context.user_data[1]
    external_id = update.message.chat_id
    name = update.message.chat.username
    # проверяем есть ли такой user, если нет добавляем
    if not get_user_record(external_id):
        add_user_record(external_id, name)
    # добавляем запись item
    add_item_record(
        profile=update.message.chat_id,
        article=article,
        item_size=context.user_data[4],
        item_name=parser.get_brand_and_name(article),
        url=parser.get_url(article),
        existence=1,
        user_price=price,
    )
    # TODO каким будет вывод пользователю
    update.message.reply_text(
        text="*Товар добавлен в ваш список.\n"
             "Выберите действие:*",
        reply_markup=get_base_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def track_existence(update, context):
    """ Отслеживаем появление товара. """
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="*Введите артикул*",
        parse_mode=ParseMode.MARKDOWN,
    )
    return TE2


def ask_size_te(update, context):
    """ Проверяем товар по артикулу и наличие размеров. """
    # получить артикул
    # проверить полученные данные
    article = validate_article(update.message.text)
    # если артикул не существует
    if article is None:
        update.message.reply_text(
            text='Пожалуйста введите корректный артикул или нажмите *"Отмена"*',
            reply_markup=get_keyboard_cancel("Отмена"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TE2
    context.user_data[1] = article
    # проверяем с размерами или без
    sizes = parser.get_sizes(article)
    # проверяем наличие товара
    item_price = validate_item_price(article)
    # если в наличии
    if item_price:
        # если с размерами
        if sizes:
            # если все размеры в наличии
            sizes_flag = [sizes[element] for element in sizes]
            if all(sizes_flag):
                update.message.reply_text(
                    text='Товар со всеми размерами в наличии. Перейдите в *"Главное меню"*',
                    reply_markup=get_keyboard_cancel("Главное меню"),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return TE2
            # если не все размеры в наличии
            context.user_data[2] = sizes
            update.message.reply_text(
                text="*Укажите размер*",
                parse_mode=ParseMode.MARKDOWN,
            )
            return TE3
        # если без размеров
        update.message.reply_text(
            text='Товар в наличии. Перейдите в *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TE2
    # если товара нет в наличии
    # если с размерами
    if sizes:
        context.user_data[2] = sizes
        update.message.reply_text(
            text="*Укажите размер*",
            parse_mode=ParseMode.MARKDOWN,
        )
        return TE3
    # если без размеров
    external_id = update.message.chat_id
    name = update.message.chat.username
    # проверяем есть ли такой user, если нет добавляем
    if not get_user_record(external_id):
        add_user_record(external_id, name)
    # добавляем в БД
    add_item_record(
        profile=external_id,
        article=article,
        item_size=0,
        item_name=parser.get_brand_and_name(article),
        url=parser.get_url(article),
        existence=0,
        user_price=0,
    )
    update.message.reply_text(
        text="*Товар добавлен в ваш список.\n"
             "Выберите действие:*",
        reply_markup=get_base_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def get_info_te(update, context):
    """ Собираем воедино полученные данные, сохраняем в БД. """
    sizes = context.user_data[2]
    answer = update.message.text
    size = validate_size(answer, sizes)
    # если введенное значение не корректно
    if size is None:
        update.message.reply_text(
            text='Пожалуйста введите корректный размер или нажмите *"Отмена"*',
            reply_markup=get_keyboard_cancel("Отмена"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TE3
    # если такой размер есть в наличии
    if sizes[size]:
        update.message.reply_text(
            text='Размер есть в наличии. Перейдите в *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return TE3
    # если запрашиваемого  размера нет
    external_id = update.message.chat_id
    name = update.message.chat.username
    # проверяем есть ли такой user, если нет добавляем
    if not get_user_record(external_id):
        add_user_record(external_id, name)
    # добавляем в БД
    article = context.user_data[1]
    add_item_record(
        profile=update.message.chat_id,
        article=article,
        item_size=size,
        item_name=parser.get_brand_and_name(article),
        url=parser.get_url(article),
        existence=0,
        user_price=0,
    )
    update.message.reply_text(
        text="*Товар добавлен в ваш список.\n"
             "Выберите действие:*",
        reply_markup=get_base_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def show_items(update, context):
    """ Смотрим свой список товаров. """
    query = update.callback_query
    query.answer()
    # узнаём данные пользователя
    external_id = query.message.chat_id
    name = query.message.chat.username
    # если нет такого user, создаём
    if not get_user_record(external_id):
        add_user_record(external_id, name)
    items = get_items(external_id)
    if not items:
        query.message.reply_text(
            text='Ваш список пока пуст. Перейдите в *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return FIRST
    items_text = utils.get_text_with_items(items)
    items_text.append('\nПосмотреть страницу с товаром можно кликнув по его названию. '
                      'Если хотите что-либо удалить из списка, *запомните его ID* '
                      'и нажмите *"Удалить"*')
    text = '\n'.join(items_text)
    query.edit_message_text(
        text=text,
        reply_markup=get_keyboard_delete_in_show_items(),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
    return FIRST


def delete_item(update, context):
    """ Удаляем товар из БД. """
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="*Введите ID товара*",
        reply_markup=get_keyboard_cancel("Главное меню"),
        parse_mode=ParseMode.MARKDOWN,
    )
    return DEL2


def delete(update, context):
    answer = update.message.text
    external_id = update.message.chat_id
    items_id = [item[0] for item in get_items_id(external_id)]
    # проверяем переданный ID
    record_id = validate_item_id(answer, items_id)
    if record_id is None:
        update.message.reply_text(
            text='Введите пожалуйста корректный *ID* или перейдите в *"Главное меню"*',
            reply_markup=get_keyboard_cancel("Главное меню"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DEL2
    delete_entry(record_id)
    update.message.reply_text(
        text="*Запись успешно удалена*",
        reply_markup=get_keyboard_cancel("Главное меню"),
        parse_mode=ParseMode.MARKDOWN,
    )
    return FIRST


def handle_daily_price_changes(context):
    """ Срабатывает по заданному времени.
        Сравниваем данные из БД с ценами на данный момент,
        и в случае снижения цены до указанной или пропажи
        товара из продажи отправляет соответствующее уведомление
    """
    items = get_price_tracking_goods()
    for profile, item_id, text in utils.get_price_status(items):
        delete_entry(item_id)
        context.bot.send_message(
            chat_id=profile,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )


def handle_daily_goods_appearances(context):
    """ Срабатывает по заданному времени.
        Проверяем появление отслеживаемых товаров, отправляет
        уведомление пользователю
    """
    items = get_tracking_goods()
    for profile, item_id, text in utils.get_appeared_goods(items):
        delete_entry(item_id)
        context.bot.send_message(
            chat_id=profile,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )


def main():
    init_db()
    updater = Updater(token=os.getenv("TG_TOKEN"))
    dp = updater.dispatcher
    jq = updater.job_queue
    # запуск проверки товаров
    jq.run_repeating(handle_daily_price_changes, 3600)
    jq.run_repeating(handle_daily_goods_appearances, 3600)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [
                CallbackQueryHandler(track_price, pattern='^' + str(TP) + '$'),
                CallbackQueryHandler(track_existence, pattern='^' + str(TE) + '$'),
                CallbackQueryHandler(show_items, pattern='^' + str(SI) + '$'),
                CallbackQueryHandler(delete_item, pattern='^' + str(DEL) + '$'),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            # TP - track price
            TP2: [
                MessageHandler(Filters.text, ask_size_tp, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            TP3: [
                MessageHandler(Filters.text, ask_price_tp, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            TP4: [
                MessageHandler(Filters.text, get_info_tp, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            # TE - track existence
            TE2: [
                MessageHandler(Filters.text, ask_size_te, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            TE3: [
                MessageHandler(Filters.text, get_info_te, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
            # DEL - delete item
            DEL2: [
                MessageHandler(Filters.text, delete, pass_chat_data=True),
                CallbackQueryHandler(start_over, pattern='^' + str(START) + '$'),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    load_dotenv()
    tg_logs_token = os.getenv("TG_LOGS_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    logger.addHandler(MyLogsHandler(tg_logs_token, tg_chat_id))
    logger.info("Бот запущен")
    while True:
        try:
            main()
        except Exception as error:
            logger.info(f"Бот упал с ошибкой, {error}")
