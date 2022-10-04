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
from typing import Optional


class AuthorizationError(Exception):
    """
    Raised when HTTP 401: Unauthorized received.
    """
    pass


class CoreConnect:
    """Class for connecting easily to InoCore and perform HTTP requests on it.

    Gets JSON Web Token and refreshes it if needed.
    Provides methods for GET, POST, PUT and DELETE.

    Attributes:
        base_url: URL of InoCore instance.
        username: Username or email address of user
        password: Password for user
        project_id: ID of project
        token: JSON Web Token for authentication
        token_expires: Time when token expires as UNIX timestamp
    """
    CLASS_VERSION = '1.0.1'
    SUPPORTED_METHODS = [
        'GET',
        'POST',
        'PUT',
        'DELETE'
    ]

    def __init__(self, base_url: str, username: str, password: str, project_id):
        """Inits CoreConnect.

        :param base_url: URL of InoCore instance.
        :param username: Username or email address of user
        :param password: Password for user
        :param project_id: ID of project
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.project_id = project_id
        self.token = ''
        self.token_expires = 0

    def get_token(self):
        """Get JSON Web Token for authentication and store it in token. Update token_expires."""
        if time.time() >= self.token_expires:
            response = requests.post(f'{self.base_url}/token',
                                     headers={'user-agent': f'MCP/{self.CLASS_VERSION}'},
                                     auth=(self.username, self.password))

            if response.status_code == HTTPStatus.UNAUTHORIZED:
                raise AuthorizationError(f'Failed to authorize. Check credentials.')

            if response.status_code != HTTPStatus.CREATED:
                raise ConnectionError(f'Cannot get token: {response.reason}')

            content_dict = json.loads(response.content)  # Deserialize content of response.
            self.token = content_dict['token']
            d = datetime.strptime(content_dict['expires']['date'], '%Y-%m-%d %H:%M:%S.%f')
            self.token_expires = d.timestamp()

    def call(self, endpoint: str, method: str, data: Optional[list] = None, params: Optional[list] = None):
        """Abstract method for HTTP request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param method: HTTP method
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :return: Content of response as Python object (mostly dict)
        """
        if method not in self.SUPPORTED_METHODS:
            raise Exception(f'Method "{method}" is not supported! Must be one of [{", ".join(self.SUPPORTED_METHODS)}]')

        if data is None:
            data = []
        if params is None:
            params = []

        self.get_token()
        url = f'{self.base_url}/{endpoint}'

        response = requests.request(method, url, headers={
            'Authorization': f'Bearer {self.token}',
            'user-agent': f'MCP/{self.CLASS_VERSION}'
        }, params=params, data=data)

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise AuthorizationError(f'Failed to authorize. Check credentials.')

        if response.status_code != HTTPStatus.OK:
            raise ConnectionError(f'Call failed: {response.reason}')
        return json.loads(response.content)

    def get(self, endpoint: str, params: Optional[list] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param params: URL parameters
        :return: Content of response as Python object (mostly dict)
        """
        if params is None:
            params = []
        return self.call(endpoint, 'GET', [], params)

    def post(self, endpoint: str, data: Optional[list] = None, params: Optional[list] = None):
        """Perform HTTP POST request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :return: Content of response as Python object (mostly dict)
        """
        if data is None:
            data = []
        if params is None:
            params = []
        return self.call(endpoint, 'POST', data, params)

    def put(self, endpoint: str, data: Optional[list] = None, params: Optional[list] = None):
        """Perform HTTP PUT request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :return: Content of response as Python object (mostly dict)
        """
        if data is None:
            data = []
        if params is None:
            params = []
        return self.call(endpoint, 'PUT', data, params)

    def delete(self, endpoint: str, params: Optional[list] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param params: URL parameters
        :return: Content of response as Python object (mostly dict)
        """
        if params is None:
            params = []
        return self.call(endpoint, 'DELETE', [], params)
