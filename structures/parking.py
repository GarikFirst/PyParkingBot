from copy import deepcopy
from datetime import datetime

from emoji import emojize


class ParkingPlace:
    def __init__(self, number) -> None:
        self.__number = number
        self.__state = 'free'
        self.__occupant = None
        self.__occupy_since = None

    @property
    def number(self):
        return self.__number

    @property
    def state(self):
        return self.__state

    @property
    def occupant(self):
        return self.__occupant

    @property
    def occupy_since(self):
        return self.__occupy_since

    def toggle_state(self, user_id: str) -> None:
        if self.__state == 'free':
            self.__state = 'reserved'
            self.__occupant = user_id
        elif self.__occupant == user_id:
            if self.__state == 'reserved':
                self.__state = 'occupied'
                self.__occupy_since = datetime.now()
            elif self.__state == 'occupied':
                self.__state = 'free'
                self.__occupant = None
                self.__occupy_since = None
        else:
            raise ValueError

    def cancel_reserve(self) -> None:
        self.__state = 'free'
        self.__occupant = None

    def clear(self) -> None:
        self.__state = 'free'
        self.__occupant = None
        self.__occupy_since = None


class Parking():
    def __init__(self, numbers: list) -> None:
        self.__places = self.__populate_parking(numbers)

    @property
    def places(self):
        return self.__places

    @property
    def state(self):
        return self.__make_state()

    @property
    def state_text(self):
        return self.__make_state_text()

    @property
    def is_free(self):
        return self.__check_free()

    def clear(self) -> list:
        places = []
        if not self.is_free:
            for place in self.__places:
                if place.state != 'free':
                    places.append(deepcopy(place))
                    place.clear()
        return places

    def __populate_parking(self, numbers: list) -> list:
        places = []
        for number in numbers:
            places.append(ParkingPlace(str(number)))
        return places

    def __check_free(self) -> bool:
        free = True
        for place in self.__places:
            if place.state != 'free':
                free = False
                break
        return free

    def __make_state(self) -> list:
        state = []
        for place in self.__places:
            place_sign = self.__make_place_sign(place)
            state.append((place_sign, place.state,
                         place.number, place.occupant))
        return state

    def __make_state_text(self) -> str:
        sort_order = {'occupied': 0, 'reserved': 1, 'free': 2}
        places = sorted(self.__places, key=lambda x: sort_order[x.state])
        state_text = ''
        for place in places:
            place_sign = self.__make_place_sign(place)
            state_text = ''.join([state_text, place_sign])
        return state_text

    def __make_place_sign(self, place: ParkingPlace) -> str:
        if place.state == 'free':
            place_sign = emojize(':green_square:')
        elif place.state == 'reserved':
            place_sign = emojize(':yellow_square:')
        elif place.state == 'occupied':
            place_sign = emojize(':red_square:')
        return place_sign
