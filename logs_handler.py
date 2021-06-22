import logging
from telegram.ext import Updater


class MyLogsHandler(logging.Handler):

    def __init__(self, tg_token, chat_id):
        super().__init__()
        self.updater = Updater(token=tg_token)
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.updater.bot.send_message(chat_id=self.chat_id, text=log_entry)
