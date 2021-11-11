from telegram import Message
from telegram.error import BadRequest


class UserView:
    """Representation of "user view".

    User view is two messages (second one is also "quick status" for preview).
    View can be update or deleted.
    """
    def __init__(self, info: Message, status: Message) -> None:
        self.__info = info
        self.__status = status

    def update(self, info: str, status: None, keyboard=None):
        """Updates messages of user's view.

        Args:
            info: first "info" message.
            status: last "status" message.
            keyboard (optional): new keyboard. Defaults to None.
        """
        if info is not None:
            self.__info.edit_text(info, parse_mode='MarkdownV2')
        if status is not None:
            self.__status.edit_text(status, parse_mode='MarkdownV2')
        if keyboard is not None:
            self.__status.edit_reply_markup(keyboard)

    def delete(self):
        """Deletes messages of user's view."""
        try:
            self.__info.delete()
            self.__status.delete()
        except BadRequest:
            pass
