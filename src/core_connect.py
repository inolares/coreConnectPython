"""
Class for connecting easily to InoCore and perform HTTP requests on it.
Written by Sascha 'SieGeL' Pfalz <s.pfalz@inolares.de> and Timo Hofmann <t.hofmann@inolares.de>
(c) 2019-2022 Inolares GmbH & Co. KG
"""
import requests
import json
import time
from datetime import datetime
from http import HTTPStatus
from typing import Optional, Union, Any, Tuple, List
from validators import url as valid_url


class AuthorizationError(Exception):
    """
    Raised when HTTP 401: Unauthorized received.
    """
    pass


class InvalidUrlException(Exception):
    """
    Raised when invalid URL given.
    """
    pass


class InvalidResponseException(Exception):
    """
    Raised when invalid response received.
    """
    pass


class CoreConnect:
    """Class for connecting easily to InoCore and perform HTTP requests on it.

    Gets JSON Web Token and refreshes it if needed.
    Provides methods for GET, POST, PUT and DELETE.

    Attributes:
        api_url: URL of InoCore instance.
        username: Username or email address of user
        password: Password for user
        project_id: ID of project
        token: JSON Web Token for authentication
        token_expires: Time when token expires as UNIX timestamp
    """
    CLASS_VERSION = '1.0.1'
    USER_AGENT = f'coreConnectPython/{CLASS_VERSION}'

    METHOD_GET = 'GET'
    METHOD_PUT = 'PUT'
    METHOD_POST = 'POST'
    METHOD_DELETE = 'DELETE'

    SUPPORTED_METHODS = [
        METHOD_GET,
        METHOD_PUT,
        METHOD_POST,
        METHOD_DELETE
    ]

    def __init__(self, api_url: str, username: str, password: str, project_id: str):
        """Inits CoreConnect.

        :param api_url: URL of InoCore instance.
        :param username: Username or email address of user
        :param password: Password for user
        :param project_id: ID of project
        """
        self.last_api_url = ''

        if not valid_url(api_url):
            raise InvalidUrlException('API URL is not valid!')

        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.project_id = project_id
        self.token = ''
        self.token_expires = 0

    def get_token(self):
        """If a valid token exists, do nothing. Otherwise, get JSON web token for authentication.

        :return: None
        """
        if time.time() >= self.token_expires or self.token == '':
            response = requests.post(f'{self.api_url}/token', headers={'user-agent': self.USER_AGENT},
                                     auth=(self.username, self.password))

            self.last_api_url = '/token'

            if response.status_code == HTTPStatus.UNAUTHORIZED:
                raise AuthorizationError(f'Failed to authorize. Check credentials.')

            if response.status_code != HTTPStatus.CREATED:
                raise ConnectionError(f'Cannot get token: {response.reason}')

            try:
                content = response.json()
            except json.JSONDecodeError:
                raise Exception('JSON error: cannot deserialize token.')

            try:
                self.token = content['token']
            except KeyError:
                raise Exception('API error: cannot get token!')

            try:
                date = content['expires']['date']
            except KeyError:
                raise Exception('API error: token does not have expire date!')

            try:
                dt = datetime.fromisoformat(date)
            except ValueError:
                raise Exception('API error: expire date is not valid ISO format!')

            self.token_expires = dt.timestamp()

    def call(self, endpoint: str, method: str, data: Optional[Union[dict, List[Tuple[str, Any]]]] = None,
             params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Abstract method for HTTP request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param method: HTTP method
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        url = f'{self.api_url}/{endpoint}'
        self.last_api_url = url

        if method not in self.SUPPORTED_METHODS:
            raise Exception(f'Method "{method}" is not supported! Must be one of [{", ".join(self.SUPPORTED_METHODS)}]')

        if not valid_url(url):
            raise InvalidUrlException(f'Error: Invalid URL {url}!')

        if data is None:
            data = {}
        if params is None:
            params = {}

        self.get_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'user-agent': f'MCP/{self.CLASS_VERSION}'
        }

        res = requests.request(method, url, headers=headers, params=params, data=data)
        return self._prepare_response(res)

    def _prepare_response(self, res: requests.Response):
        """Parse response of API.

        :param res: request.Response object
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Decode response content, if response was valid.
        """
        if res.status_code == HTTPStatus.UNAUTHORIZED:
            raise AuthorizationError(f'Failed to authorize. Check credentials.')

        # if res.status_code != HTTPStatus.OK:
        #     raise ConnectionError(f'Call failed: {res.reason}')

        try:
            content = res.json()
        except json.JSONDecodeError:
            raise ValueError('JSON error: Cannot decode response content.')

        if 'statusCode' not in content:
            raise InvalidResponseException(f'API error: Invalid response: {res.status_code} {self.last_api_url}')

        try:
            data = content['data']
        except KeyError:
            try:
                emsg = f"{content['error']['description']}. {res.status_code} {self.last_api_url}"
                raise InvalidResponseException(emsg)
            except KeyError:
                raise InvalidResponseException(f'Invalid response: {res.status_code} {self.last_api_url}')

        if 'error' in data:
            raise InvalidResponseException(f"{data['error']}. {res.status_code} {self.last_api_url}")

        return content

    def get(self, endpoint: str, params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        if params is None:
            params = {}
        return self.call(endpoint, 'GET', {}, params)

    def post(self, endpoint: str, data: Optional[Union[dict, List[Tuple[str, Any]]]] = None,
             params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP POST request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        if data is None:
            data = {}
        if params is None:
            params = {}
        return self.call(endpoint, 'POST', data, params)

    def put(self, endpoint: str, data: Optional[Union[dict, List[Tuple[str, Any]]]] = None,
            params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP PUT request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        if data is None:
            data = {}
        if params is None:
            params = {}
        return self.call(endpoint, 'PUT', data, params)

    def delete(self, endpoint: str, params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        if params is None:
            params = {}
        return self.call(endpoint, 'DELETE', {}, params)
