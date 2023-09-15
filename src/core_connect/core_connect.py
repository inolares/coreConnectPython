"""
Class for connecting easily to InoCore and perform HTTP requests on it.
Written by Timo Hofmann <t.hofmann@inolares.de> and Sascha 'SieGeL' Pfalz <s.pfalz@inolares.de>
(c) 2019-2023 Inolares GmbH & Co. KG
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


class InvalidMethodException(Exception):
    """
    Raised when invalid method given.
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
        verify_peer: When False, TLS will not be verified, so you can use self-signed TLS certificates. ONLY use
                            when you know what you are doing.
        return_object: When true, returns Response object instead of JSON.
    """
    CLASS_VERSION = '2.1.1'
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

    # Instead we could also use Response.ok() or Response.raise_for_status(). Those check if status_code < 400.
    SUCCESSFUL_RESPONSE_CODES = [
        HTTPStatus.OK,
        HTTPStatus.CREATED,
        HTTPStatus.ACCEPTED,
        HTTPStatus.NON_AUTHORITATIVE_INFORMATION,
        HTTPStatus.NO_CONTENT
    ]

    def __init__(self, api_url: str, username: str, password: str, project_id: str, verify_peer: bool = True,
                 return_object: bool = False):
        """Inits CoreConnect.

        :param api_url: URL of InoCore instance.
        :param username: Username or email address of user
        :param password: Password for user
        :param project_id: ID of project
        :param verify_peer: When False, TLS will not be verified, so you can use self-signed TLS certificates. ONLY use
                            when you know what you are doing.
        :param return_object: When true, returns Response object instead of JSON.
        """
        self.last_api_url = ''

        if not valid_url(api_url):
            raise InvalidUrlException('API URL is not valid.')

        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.project_id = project_id
        self.token = ''
        self.token_expires = 0
        self.verify_peer = verify_peer
        self.return_object = return_object

    def get_token(self):
        """If a valid token exists, do nothing. Otherwise, get JSON web token for authentication.

        :return: None
        """
        if time.time() >= self.token_expires or self.token == '':
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'user-agent': self.USER_AGENT
            }
            res = requests.post(f'{self.api_url}/token',
                                     headers=headers,
                                     auth=(self.username, self.password),
                                     verify=self.verify_peer)

            self.last_api_url = '/token'

            if res.status_code == HTTPStatus.UNAUTHORIZED:
                raise AuthorizationError(f'Failed to authorize. Check credentials.')

            if res.status_code != HTTPStatus.CREATED:
                self._raise_invalid_response(res.status_code, res.reason, 'Could not get token.')

            try:
                content = res.json()
            except json.JSONDecodeError:
                self._raise_invalid_response(res.status_code, res.reason, 'JSON Error: Cannot deserialize token.')

            try:
                self.token = content['token']
            except KeyError:
                self._raise_invalid_response(res.status_code, res.reason, 'API Error: Cannot get token.')

            try:
                date = content['expires']['date']
            except KeyError:
                self._raise_invalid_response(res.status_code, res.reason, 'API Error: Token does not have expire date.')

            try:
                dt = datetime.fromisoformat(date)
            except ValueError:
                self._raise_invalid_response(res.status_code, res.reason,'API Error: Expire date is not valid ISO format.')

            self.token_expires = dt.timestamp()

    def _call(self, endpoint: str, method: str, data: Optional[Union[dict, List[Tuple[str, Any]]]] = None,
             params: Optional[Union[dict, List[Tuple[str, Any]]]] = None) -> Union[dict, requests.Response]:
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

        if method not in self.SUPPORTED_METHODS:
            raise InvalidMethodException(f'Method "{method}" is not supported. Must be one of [{", ".join(self.SUPPORTED_METHODS)}].')

        if not valid_url(url):
            raise InvalidUrlException(f'Invalid URL {url}.')

        if data is None:
            data = {}
        if params is None:
            params = {}

        self.get_token()
        self.last_api_url = url

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
            'user-agent': self.USER_AGENT
        }

        # Add params to URL.
        if params:
            url += self._add_params(params)

        res = requests.request(method, url, headers=headers, json=data)
        if self.return_object:
            return res
        return self._prepare_response(res)

    @staticmethod
    def _add_params(params: dict) -> str:
        """Return query parameter as string to be added to URL. String is not yet URL encoded!

        :param params: The URL query parameters.
        :return: Query parameters as string, ready to be added to URL and to be URL encoded.
        """
        result = '?'

        for option, value in params.items():

            # E.g. list of filters
            if isinstance(value, list):
                for i, v in enumerate(value):
                    if isinstance(v, dict):
                        for key, val in v.items():
                            result += f'{option}[{i}][{key}]={val}&'
                    # 1-dimensional values.
                    elif isinstance(v, int) or isinstance(v, float) or isinstance(v, str):
                        result += f'{option}[{i}]={v}&'
                    # TODO: Other types than dict, int, float and str, e.g. lists.

            # TODO: Implement dict.
            elif isinstance(value, dict):
                continue

            # 1-dimensional option, e.g. value type int, float or str.
            else:
                result += f'{option}={value}&'

        return result.rstrip('&')

    def _prepare_response(self, res: requests.Response) -> dict:
        """Parse response of API.

        :param res: request.Response object
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Decode response content, if response was valid.
        """
        if res.status_code == HTTPStatus.UNAUTHORIZED:
            raise AuthorizationError(f'Failed to authorize. Check credentials.')

        if res.status_code not in self.SUCCESSFUL_RESPONSE_CODES:
            self._raise_invalid_response(res.status_code, res.reason, res.text)

        try:
            content = res.json()
        except json.JSONDecodeError:
            self._raise_invalid_response(res.status_code, res.reason, f'JSON error: f{res.text}')

        if 'statusCode' not in content:
            raise self._raise_invalid_response(res.status_code, res.reason, f'{content}')

        try:
            data = content['data']
        except KeyError:
            try:
                self._raise_invalid_response(res.status_code, res.reason, f"{content['error']}")
            except KeyError:
                self._raise_invalid_response(res.status_code, res.reason, f'{content}')

        if 'error' in data:
            self._raise_invalid_response(res.status_code, res.reason, f"{content['error']}")

        return content

    def _raise_invalid_response(self, status_code: int, reason: str, msg: str = None):
        """Print msg when given. Raise InvalidResponseException with HTTP status code, HTTP reason and the called URL.

        :param status_code: HTTP status code.
        :param reason: HTTP reason/description.
        :param msg: Optional message, e.g. Response as plain text.
        :raises: InvalidResponseException
        :return: None
        """
        if msg:
            print(msg)
        raise InvalidResponseException(f'HTTP {status_code} {reason}: {self.last_api_url}')

    def get(self, endpoint: str, params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        return self._call(endpoint, self.METHOD_GET, {}, params)

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
        return self._call(endpoint, self.METHOD_POST, data, params)

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
        return self._call(endpoint, self.METHOD_PUT, data, params)

    def delete(self, endpoint: str, data: Optional[Union[dict, List[Tuple[str, Any]]]] = None,
               params: Optional[Union[dict, List[Tuple[str, Any]]]] = None):
        """Perform HTTP GET request.

        :param endpoint: Path of API endpoint (e.g. v1/daemons)
        :param data: Data to be sent to server in request body
        :param params: URL parameters
        :raise AuthorizationError: Invalid credentials given.
        :raise ValueError: Decoding response content failed.
        :return: Content of response as Python object (mostly dict)
        """
        return self._call(endpoint, self.METHOD_DELETE, data, params)
