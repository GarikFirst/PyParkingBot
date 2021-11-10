from telegram import Message
from telegram.error import BadRequest


class UserView:
    def __init__(self, info: Message, status: Message) -> None:
        self.__info = info
        self.__status = status

    @property
    def info(self):
        return self.__info

    def update(self, info: str, status: None, keyboard=None):
        if info is not None:
            self.__info.edit_text(info, parse_mode='MarkdownV2')
        if status is not None:
            self.__status.edit_text(status, parse_mode='MarkdownV2')
        if keyboard is not None:
            self.__status.edit_reply_markup(keyboard)

    def delete(self):
        try:
            self.__info.delete()
            self.__status.delete()
        except BadRequest:
            pass
