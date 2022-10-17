import time
from src import core_connect
from pprint import pprint


URL = 'url'
USER = 'user'
PASS = 'password'
PROJECT_ID = 'project_id'


def main():
    cc = core_connect.CoreConnect(URL, USER, PASS, PROJECT_ID)
    # cc.get_token()
    # time.sleep(5)
    # cc.get_token()
    print(cc.get(f'v1/daemon/mcp_status/{PROJECT_ID}'))


if __name__ == '__main__':
    main()
