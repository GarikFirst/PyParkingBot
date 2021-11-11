from copy import deepcopy
from datetime import datetime

from emoji import emojize


class ParkingPlace:
    """Representation of parking place.

    Attributes:
        number: place number.

    Logic is really simple - each place has three states:
    - free
    - reserved
    - occupied

    and can toggle between them (free -> reserved -> occupied -> free).
    Since place reserved or occupied no other user can take this place.
    Also user can cancel reserve.
    """
    def __init__(self, number: str) -> None:
        self.__number = number
        self.__state = 'free'
        self.__occupant = None
        self.__occupy_since = None

    @property
    def number(self) -> str:
        return self.__number

    @property
    def state(self) -> str:
        return self.__state

    @property
    def occupant(self) -> str:
        return self.__occupant

    @property
    def occupy_since(self) -> datetime:
        return self.__occupy_since

    def toggle_state(self, user_id: str) -> None:
        """Toggles place state.

        Args:
            user_id: user_id for for check possibility of state change.

        Raises:
            ValueError: if user wants place that not free and
            don't belong to him.
        """
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

    def cancel_reserve(self, user: str) -> None:
        """Cancel the reserve and change place state to free.

        Args:
            user: user_id for check possibility of canceling the reserve.

        Raises:
            ValueError: if place don't belong to user (it means that
            user press button on old keyboard).
        """
        if self.__occupant == user and self.state == 'reserved':
            self.__state = 'free'
            self.__occupant = None
        else:
            raise ValueError

    def clear(self) -> None:
        """For "clearing" the place without rights check."""
        self.__state = 'free'
        self.__occupant = None
        self.__occupy_since = None


class Parking():
    """Representation of the parking lot.

    Can be cleared (all places set to free without rights check).
    """
    def __init__(self, numbers: list) -> None:
        self.__places = self.__populate_parking(numbers)

    @property
    def places(self) -> list:
        return self.__places

    @property
    def state(self) -> list:
        """For keyboard making.

        Returns:
            list: list of tuples for place representation while
            making keyboard.
        """
        return self.__make_state()

    @property
    def state_text(self) -> str:
        """Text state for "status" message"""
        return self.__make_state_text()

    @property
    def is_free(self) -> bool:
        """Is parking free."""
        return self.__check_free()

    def clear(self) -> list:
        """Free all places of parking.

        Raises:
            ValueError: if there is no not free places (it means that
            user press button on old keyboard).

        Returns:
            list: copy of places that have been cleared for statistics count.
        """
        places = []
        if not self.is_free:
            for place in self.__places:
                if place.state != 'free':
                    places.append(deepcopy(place))
                    place.clear()
        else:
            raise ValueError
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
