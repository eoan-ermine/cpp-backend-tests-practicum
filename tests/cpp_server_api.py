import json

import requests

from urllib.parse import urljoin
from pathlib import Path
from typing import Optional, Tuple, List, Union, Type, KeysView, Any


class ServerException(Exception):
    def __init__(self, message: str, data: Any):
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

    def __init__(self, parent_object: str, expected: Any, given: Any):
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
    def __init__(self, parent_object: str, expected_type: Union[Type, List[Type]], given_type: Type):

        expected_type = [t.__name__ for t in list(expected_type)]

        super().__init__(f"{parent_object} has wrong fields",
                         {'expected type': expected_type, 'given type': given_type.__name__})

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
        return f"{self.parent_object} has wrong type:\n{json.dumps(self.expected_type)} was expected, " \
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

        CppServer.assert_type('Map list', list, res_json)

        for m in res_json:
            CppServer.assert_fields('Map', ['id', 'name'], m.keys())
            CppServer.assert_type('Map id', str, m['id'])
            CppServer.assert_type('Map name', str, m['name'])

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

        CppServer.assert_fields('Join game response', ['authToken', 'playerId'], res_json.keys())

        token = res_json['authToken']
        self.validate_token(token)

        player_id = res_json['playerId']
        CppServer.assert_type('Player id', int, player_id)

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
        res_json = res.json()
        self.validate_state(res_json)
        return res_json

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

    @staticmethod
    def assert_type(obj_name: str, expected_types: Union[Type, List[Type]], obj: any):
        if type(expected_types) not in {list, tuple, set}:
            expected_types = [expected_types]
        if type(obj) not in expected_types:
            raise WrongType(obj_name, expected_types, type(obj))

    @staticmethod
    def assert_fields(object_name, expected_keys: Union[list, str, KeysView], given_keys: KeysView):
        for key in list(expected_keys):
            if key not in given_keys:
                raise WrongFields(object_name, list(expected_keys), list(given_keys))

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

        CppServer.assert_fields('Map', expected.keys(), m.keys())

        for key in expected.keys():
            CppServer.assert_type(key, expected[key], m[key])

        extra = {'dogSpeed': float}

        for key in extra:
            if key in m.keys():
                CppServer.assert_type(key, extra[key], m[key])

        dog_speed = m.get('dogSpeed')
        if dog_speed is not None:
            if dog_speed < 0:
                raise DataInconsistency('Dog speed can\'t be negative', {'dog speed': dog_speed})

        for road in m['roads']:
            road: dict
            CppServer.assert_type('Road', dict, type(road))

            if road.keys() != {'x0', 'y0', 'x1'} and road.keys() != {'x0', 'y0', 'y1'}:
                raise WrongFields('Road', '["x0", "y0", "x1"] or ["x0", "y0", "y1"]', list(road.keys()))

            for coordinate in road:
                CppServer.assert_type(f'Road coordinate {coordinate}', [float, int], coordinate)

        # Same for office and buildings if it's fine

    @staticmethod
    def validate_token(token: str):
        pass

    @staticmethod
    def validate_state(res_json: dict):
        print(res_json)
        CppServer.assert_type('Game state', dict, res_json)

        players = res_json.get('players')
        CppServer.assert_type('Game state, players', dict, players)
        for player_id in players:
            CppServer.assert_type('Player id', [str, int], player_id)

            player: dict = players[player_id]

            CppServer.assert_type('player_id', dict, player)

            expected = {'pos': list, 'speed': list, 'dir': str}
            for key in expected:
                CppServer.assert_fields(f'Player {player_id} state', expected.keys(), player.keys())
                CppServer.assert_type(key, expected[key], player[key])

            for coordinate in player['pos']:
                CppServer.assert_type('Player position', float, coordinate)
            for coordinate in player['speed']:
                CppServer.assert_type('Player speed', float, coordinate)

            CppServer.assert_type('Player direction', str, player['dir'])
            expected_dirs = ['R', 'L', 'U', 'D', '']
            if player['dir'] not in expected_dirs:
                raise UnexpectedData('Player direction', ['R', 'L', 'U', 'D', ''], player['dir'])
