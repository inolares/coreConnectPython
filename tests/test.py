import time
from src import core_connect
from pprint import pprint


URL = 'http://localhost:8080/'
USER = 'daemon@localhost'
PASS = 'daemon2k22'
PROJECT_ID = 'tEsT@ino'


def main():
    cc = core_connect.CoreConnect(URL, USER, PASS, PROJECT_ID)
    # cc.get_token()
    # time.sleep(5)
    # cc.get_token()
    print(cc.get(f'v1/daemon/mcp_status/{PROJECT_ID}'))


if __name__ == '__main__':
    main()