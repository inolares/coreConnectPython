import time
from core_connect import CoreConnect


URL = 'http://localhost:8080/'
USER = 'daemon@localhost'
PASS = 'daemon2k22'
PROJECT_ID = 'tEsT@ino'


def main():
    cc = CoreConnect(URL, USER, PASS, PROJECT_ID)
    cc.get_token()
    time.sleep(5)
    cc.get_token()


if __name__ == '__main__':
    main()
