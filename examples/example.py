"""
Little example from README. To make it work, you need a running InoCore instance and fill out the url, user, password
and project_id below.

Written by Timo Hofmann <t.hofmann@inolares.de>
(c) 2023 Inolares GmbH & Co. KG
"""
from pprint import pprint
from src import core_connect

URL = 'url'
USER = 'user'
PASS = 'password'
PROJECT_ID = 'project_id'


def main():
    cc = core_connect.CoreConnect(URL, USER, PASS, PROJECT_ID)
    pprint(cc.get('v1/ping'))

    data = {
        'project_id': 'nice_project',
        'bus_type': 'MODBUS',
        'hostname': '192.168.1.2',
        'port': 502,
        'name': 'high end DDC'
    }

    pprint(cc.post('v1/bus_config', data=data))


if __name__ == '__main__':
    main()
