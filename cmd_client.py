#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
import socket
# import threading
# from time import sleep
from datetime import datetime

'''

class SockClient(threading.Thread):
    def __init__(self, host_ip, host_port):
        threading.Thread.__init__(self)
        self.running = False
        self.sock = socket.socket()
        self.sock.settimeout(20)  # 20 seconds
        try:
            self.sock.connect((host_ip, host_port))
        except socket.error, e:
            print("Socket Connect Error:%s" % e)
            exit(1)
        print("connect success")
        self.running = True

        self.error_cnt = 0

    def run(self):
        while self.running:
            try:
                send_data = '\x12\x34\x56'
                self.sock.send(send_data)
                data = self.sock.recv(1024)
                if len(data) > 0:
                    self.error_cnt = 0
                    recv_data = data.encode('hex')
                    print 'recv:', recv_data
                sleep(1)

            except socket.error, e:
                print 'socket running error:', str(e)
                break
        print 'SockClient Thread Exit\n'

'''


# def text_search(types, sort_field, search_txt):



if __name__ == "__main__":

    # print datetime.now()
    method = "text_search"
    types = "cmds"
    sort_field = "num"
    search_txt = " ".join(sys.argv[1:])
    search = ";".join([method, search_txt, types, sort_field])

    HOST='localhost'
    PORT = 21590
    socket1 = socket.socket()
    socket1.connect((HOST, PORT))
    socket1.send(search)
    data = socket1.recv(65536)
    # print datetime.now()
    print data



    '''
    sock_client = SockClient('192.168.99.219', 8093)
    sock_client.start()

    try:
        while True:
            sleep(1)

            if not sock_client.is_alive():
                break

    except KeyboardInterrupt:
        print 'ctrl+c'
        sock_client.running = False
    sock_client.join()
    print 'exit finally'
    '''
