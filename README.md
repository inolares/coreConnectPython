# CoreConnect - Helper class to communicate with InoCore #

This PIP package provides the `CoreConnect` class to easily communicate with an InoCore installation.

## Requirements ##

- Python 3.8 or newer
- requests package

## Installation ##

Make sure your PIP is up-to-date:

```python -m install --upgrade pip```

To install it:

```python -m pip install coreconnect```

## Usage ##

The usage is pretty straight forward. Make sure to import the class:

```from coreconnect import CoreConnect```

Now you can create a `CoreConnect` object with the InoCore URL, your InoCore credentials and the current project id:

`cc = CoreConnect(url, username, password, project_id)`

With that you can easily make InoCore API request with the according HTTP method. For example:

```
cc.get('v1/ping') 
cc.post('v1/bus_config')
```

## Class methods ##

The following methods are implemented:

- call()
- get()
- post()
- put()
- delete()


