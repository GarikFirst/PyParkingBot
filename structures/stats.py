from datetime import date, datetime, timedelta

from emoji import emojize

from .parking import ParkingPlace


class Stats:
    def __init__(self, users: dict) -> None:
        self.__users = users
        self.__places = {}
        self.__persons = {}
        self.__weekdays = {}
        self.__monthes = {}
        self.__total_time = 0.0

    @property
    def message_text(self):
        return self.__make_message_text()

    def count(self, place: ParkingPlace) -> None:
        today = date.today()
        if place.state == 'reserved':
            self.__places[place.number] = self.__places.get(
                place.number, 0) + 1
            self.__persons[place.occupant] = self.__persons.get(
                place.occupant, 0) + 1
            self.__weekdays[today.strftime('%A')] = self.__weekdays.get(
                today.strftime('%A'), 0) + 1
            self.__monthes[today.strftime('%B')] = self.__monthes.get(
                today.strftime('%B'), 0) + 1
        elif place.state == 'occupied':
            self.__total_time = self.__total_time + (
                datetime.today() - place.occupy_since).total_seconds()

    def __make(self) -> tuple:
        return (self.__total_time, self.__rank(self.__places),
                self.__rank(self.__persons), self.__rank(self.__weekdays),
                self.__rank(self.__monthes))

    def __rank(self, slice: dict) -> list:
        return sorted(slice.items(), key=lambda tup: tup[1], reverse=True)

    def __make_message_text(self) -> str:
        total_time, places, persons, weekdays, monthes = self.__make()
        total_time = ':'.join(str(timedelta(0, total_time)).split(':')[:2])
        places = self.__make_message_text_block(places)
        persons = self.__make_message_text_block(persons, self.__users)
        weekdays = self.__make_message_text_block(weekdays)
        monthes = self.__make_message_text_block(monthes)
        return '\n\n'.join([
                         ' '.join([emojize(':bar_chart:'), f'**Статистика**']),
                         ' '.join([emojize(':stopwatch:'),
                                  f'**Суммарное время**: {total_time}']),
                         ' '.join([emojize(':P_button:'),
                                  f'**Места**{places}']),
                         ' '.join([emojize(':bust_in_silhouette:'),
                                  f'**Люди**{persons}']),
                         ' '.join([emojize(':tear-off_calendar:'),
                                  f'**Дни недели**{weekdays}']),
                         ' '.join([emojize(':spiral_calendar:'),
                                  f'**Месяцы**{monthes}'])])

    def __make_message_text_block(self, block: list, users=None) -> str:
        text = ''
        for num, entry in enumerate(block, start=1):
            item, value = entry
            if users is not None:
                item = self.__users[item]
            text = '\n'.join([text, ' '.join([str(num) +
                             r'\.', str(item), r'\- ' + str(value)])])
        return text
