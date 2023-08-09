# CoreConnect - Python helper class to communicate with InoCore #

This PIP package provides the `CoreConnect` class to easily communicate with an InoCore installation.

## Requirements ##

- Python 3.8 or newer

## Installation ##

Make sure your PIP is up-to-date:

```python -m install --upgrade pip```

To install it:

```python -m pip install core_connect```

## Usage ##
### Basic ###

The usage is pretty straight forward. Make sure to import the class:

```python
>>> from core_connect import CoreConnect
```

Now you can create a `CoreConnect` object with the InoCore URL, your InoCore credentials and the current project id:

```python
>>> cc = CoreConnect(url, username, password, project_id)
```

With that you can easily make InoCore API request with the according HTTP method. The methods will return the deserialized content of the response body. For example:

```python
>>> cc.get('v1/ping')
{'data': {'PONG': 1691587400.685406}, 'statusCode': 200}

# data has to be a JSON-serializable object like a dict or a list.
>>> data = {
      'project_id': 'nice_project',
      'bus_type': 'MODBUS',
      'hostname': '192.168.1.2',
      'port': 502,
      'name': 'high end DDC'
    }

>>> cc.post('v1/bus_config', data=data)

{
    'data': {
        'object': {
            'bus_type': 'MODBUS',
            'hostname': '192.168.1.2',
            'id': 160,
            'is_offline': False,
            'name': 'high end DDC',
            'node_id': -1,
            'packet_size': 0,
            'port': 502,
            'project_id': 'nice_project',
            'protocol': 'tcp',
            'ref_user_id': 1,
            'status': 1
        },
        'status': 'OK'
    },
    'statusCode': 200
}
```

Per default the methods will return the deserialized content of the response body on success. On failure an Exception will be raised. The kind of Exception raised can give a hint where the error might have happened:

- `InvalidUrlException:` The InoCore URL or the URL resulting from adding the endpoint in a call is not valid.
- `AuthorizationError:` You provided wrong credentials or your user does not have access on specified API endpoint.
- `InvalidResponseException:` The client received an invalid response from InoCore. That might be the case when we received malformed JSON for example, but also more commonly when we received a response with a HTTP status code that is not 2xx. In that case the HTTP status code will be printed as well as the error message from InoCore if there is any.

### Advanced ### 
#### Response object ###
Instead of returning the deserialized response body, you can also receive the whole `requests.Response` object from the call. That gives you more flexibility. To do so, you just need to set the parameter `return_object=True` when initializing the `CoreConnect` object.
#### Self-signed TLS ####
You can also allow connections to InoCore instances that use self-signed TLS certificates. To do that you just need to set the parameter `verify_peer=False` when initializing the `CoreConnect` object. ONLY do that if you are in a secure network and you know what you are doing!  

## Class methods ##

The following methods are implemented:

```python
get(endpoint, params=None)

post(endpoint, data=None, params=None)

put(endpoint, data=None, params=None)

delete(endpoint, data=None, params=None)
```
Whereas `data` has to be JSON-serializable. For filtering, sorting limiting and using offset you can use `params` in that form:
```python
params = {
    'filter': [
        {'property': 'project_id', 'expression': 'ilike', 'value': 'nice_project'},
        {'property': 'project_id', 'expression': 'ilike', 'value': 'nice_project_2'},
    ],
    'sort': [
        {'property': 'id', 'direction': 'asc'},
        {'property': 'name', 'direction': 'desc'},
    ],
    'limit': 10,
    'offset': 5,
}
```
As you can see, you can filter and sort by multiple properties. 

