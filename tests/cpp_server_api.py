import json

import requests

from urllib.parse import urljoin
from pathlib import Path
from typing import Optional, Tuple, List


class ServerException(Exception):
    def __init__(self, message, data):
        super().__init__()
        self.__message = message
        self.__data = data
        self.args = message, data

    @property
    def message(self):
        """
        """
        return self.__message

    @property
    def data(self):
        """
        """
        return self.__data

    def __str__(self):
        return f"{self.message}: {json.dumps(self.data)}"


class DataInconsistency(ServerException):
    """
    Given data doesn't have all the expected fields or values are not sufficient
    """


class UnexpectedData(DataInconsistency):
    """
    One of the field is missing
    """

    def __init__(self, parent_object, expected, given):
        super().__init__(f"{parent_object} has unexpected data",
                         {'expected': expected, 'given': given})
        self.__parent_object = parent_object
        self.__expected = expected
        self.__given = given
        self.args = parent_object, expected, given

    @property
    def parent_object(self):
        """

        """
        return self.__parent_object

    @property
    def expected(self):
        """

        """
        return self.__expected

    @property
    def given(self):
        """

        """
        return self.__given

    def __str__(self):
        return f"{self.parent_object} has unexpected data:\n{json.dumps(self.expected)} was expected, " \
               f"but {json.dumps(self.given)} was given"


class WrongFields(UnexpectedData):
    """
    One of the field is missing
    """

    def __str__(self):
        return f"{self.parent_object} has wrong fields:\n{json.dumps(self.expected)} was expected, " \
               f"but {json.dumps(self.given)} was given"


class WrongType(DataInconsistency):
    """
    """
    def __init__(self, parent_object, expected_type: type, given_type: type):
        super().__init__(f"{parent_object} has wrong fields",
                         {'expected type': expected_type.__name__, 'given type': given_type.__name__})
        self.__parent_object = parent_object
        self.__expected_type = expected_type
        self.__given_type = given_type
        self.args = parent_object, expected_type, given_type

    @property
    def parent_object(self):
        """
        """
        return self.__parent_object

    @property
    def expected_type(self):
        """
        """
        return self.__expected_type

    @property
    def given_type(self):
        """

        """
        return self.__given_type

    def __str__(self):
        return f"{self.parent_object} has wrong type:\n{json.dumps(self.expected_type.__name__)} was expected, " \
               f"but it's {json.dumps(self.given_type.__name__)}"


class BadRequest(ServerException):
    """
    The request was bad - token is wrong or missing, url isn't valid, etc.
    """


"""
Нижеследующие уберу, пока ещё сидят тут, посколько на них ссылаются куски кода, которые ещё не переделал
"""


class WrongHeaders(ValueError, KeyError):
    """Header doesn't have proper content-type, cache-control, or/and content-length"""


class WrongCode(ValueError):
    """The responses status code is wrong"""


class BadlyEncodedJson(json.decoder.JSONDecodeError):
    """The content isn't encoded right"""


class BadResponse(ValueError):
    """The content of the response doesn't match the expected structure or values"""


class CppServer:

    def __init__(self, url: str, output: Optional[Path] = None):
        self.url = url
        if output:
            self.file = open(output)

    def get_line(self):
        return self.file.readline()

    def get_log(self):
        return json.loads(self.get_line())

    def request(self, method, header, url, **kwargs):
        try:
            req = requests.Request(method, urljoin(self.url, url), headers=header, **kwargs).prepare()
            with requests.Session() as session:
                return session.send(req)
        except Exception as ex:
            print(ex)

    def get(self, endpoint):
        return requests.get(urljoin(self.url, endpoint))

    def post(self, endpoint, data):
        return requests.post(urljoin(self.url, endpoint), data)

    def get_maps(self) -> Optional[List[dict]]:
        request = 'api/v1/maps'
        res: requests.Response = self.get(request)
        self.validate_response(res)
        res_json: List[dict] = res.json()

        if type(res_json) != list:
            raise WrongType('Map list', list, type(res_json))
        for m in res_json:
            if set(m.keys()) == {'id', 'name'}:
                raise WrongFields('Map', ['id', 'name'], list(m.keys()))

        return res_json

    def get_map(self, map_id: str) -> Optional[dict]:
        request = 'api/v1/maps/' + map_id
        res: requests.Response = self.get(request)
        self.validate_response(res)
        self.validate_map(res.json())
        return res.json()

    def join(self, player_name: str, map_id: str) -> Tuple[str, int]:
        request = 'api/v1/game/join'
        header = {'content-type': 'application/json'}
        data = {"userName": player_name, "mapId": map_id}
        res = self.request('POST', header, request, json=data)
        res_json: dict = res.json()

        if res_json.keys() != {'authToken', 'playerId'}:
            raise WrongFields('Join game response', ['authToken', 'playerId'], list(res_json.keys()))

        token = res_json['authToken']
        self.validate_token(token)

        player_id = res_json['playerId']
        if type(player_id) != int:
            raise WrongType('Player id', int, type(player_id))

        return token, player_id

    def add_player(self, player_name: str, map_id: str) -> Tuple[str, int]:
        params = self.join(player_name, map_id)
        # Temporary "fix"
        return params

    def get_state(self, token: str) -> Optional[dict]:
        request = '/api/v1/game/state'
        header = {'content-type': 'application/json',
                  'Authorization': f'Bearer {token}'}

        res = self.request('GET', header, request)
        self.validate_response(res)

        return res.json()

    def get_player_state(self, token: str, player_id: int) -> Optional[dict]:
        game_session_state = self.get_state(token)
        players = game_session_state.get('players')

        try:
            state = players[str(player_id)]
        except KeyError:
            raise BadResponse(f'The given game session state doesn\'t '
                              f'have the desired player id "{player_id}": {players}')
        except AttributeError:
            raise BadResponse(f'The given game session state doesn\'t '
                              f'appear to have "players" field: {game_session_state}')

        return state

    def move(self, token: str, direction: str):
        request = '/api/v1/game/player/action'
        header = {'content-type': 'application/json', 'Authorization': f'Bearer {token}'}
        data = {"move": direction}
        res = self.request('POST', header, request, json=data)
        self.validate_response(res)

    def tick(self, ticks: int):
        request = 'api/v1/game/tick'
        header = {'content-type': 'application/json'}
        data = {"timeDelta": ticks}
        res = self.request('POST', header, request, json=data)
        self.validate_response(res)

    # Wil be rewritten soon
    @staticmethod
    def validate_response(res: requests.Response):
        if res.status_code != 200:
            raise WrongCode(f'Status code isn\'t OK: 200 != {res.status_code}')
        try:
            if res.headers['content-type'] != 'application/json':
                raise WrongHeaders(f'Wrong Content-Type header: '   # Should it be split into four different exceptions?
                                   f'"{res.headers["content-type"]}" instead of "application/json"')
            if res.headers['cache-control'] != 'no-cache':
                raise WrongHeaders(f'Wrong Cache-Control header: '
                                   f'"{res.headers["cache-control"]}" instead of "no-cache"')
            if res.request.method != 'HEAD':
                if int(res.headers['content-length']) != len(res.content):
                    raise WrongHeaders(f'Wrong content length: '
                                       f'"{res.headers["content-length"]}" instead of "{len(res.content)}"')
            else:
                if res.headers['content-length'] != 0:
                    raise WrongHeaders(f'Wrong content length: '
                                       f'"{res.headers["content-length"]}" instead of "0" for HEAD request')
        except KeyError as ke:
            raise WrongHeaders(f'Wrong response headers: missing "{ke.args[0]}". Headers: {res.headers}')

        try:
            res.json()
        except json.decoder.JSONDecodeError as je:
            raise BadlyEncodedJson(msg=je.msg, doc=je.doc, pos=je.pos)

    @staticmethod
    def validate_map(m: dict):
        expected = {'id': str, 'name': str, 'roads': list, 'buildings': list, 'offices': list}

        for key in expected.keys():
            if key not in m.keys():
                raise WrongFields('Map', list(expected.keys()), list(m.keys()))

            if type(m[key]) != expected[key]:
                raise WrongType(f'Map {key}', expected[key], type(m[key]))

        extra = {'dogSpeed': float}

        for key in extra:
            if key in m.keys():
                if type(m[key]) != extra[key]:
                    raise WrongType(f'Map {key}', extra[key], type(m[key]))

        for road in m['roads']:
            road: dict
            if type(road) != dict:
                raise WrongType('Road', dict, type(road))

            if road.keys() != {'x0', 'y0', 'x1'} and road.keys() != {'x0', 'y0', 'y1'}:
                raise WrongFields('Road', '["x0", "y0", "x1"] or ["x0", "y0", "y1"]', list(road.keys()))
            for coordinate in road:
                if type(road[coordinate]) not in {float, int}:
                    raise WrongType(f"Road coordinate {coordinate}", float, type(road[coordinate]))

        # Same for office and buildings if it's fine

    @staticmethod
    def validate_token(token: str):
        pass
