# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

from cmd_mongo_api import CmdMongo
from socket import *
from time import ctime
import threading
import time

HOST=''
PORT=21590
BUFSIZ=1024
ADDR = (HOST,PORT)

tcpSerSock=socket(AF_INET,SOCK_STREAM)
tcpSerSock.bind(ADDR)
tcpSerSock.listen(5)
socks=[]

cmd_api = CmdMongo(None)

def handle():
    while True:
        time.sleep(0.01)
        for s in socks:
            try:
                data = s.recv(BUFSIZ)
            except Exception, e:
                continue
            if not data:
                socks.remove(s)
                continue
            data_result = "no return"

            try:
                method = data.split(";")[0]
                # print data
                if method == "text_search":
                    [method,string,types,sort_field] = data.split(";")
                    data_result= cmd_api.text_search(string, types, sort_field="num")
                if method == "text_insert":
                    [method,string,types] = data.split(";")
                    data_result= cmd_api.text_insert(string, types, sort_field="num")
                if method == "text_update":
                    [method,string,dir,num] = data.split(";")
                    dir_id = cmd_api.dir_update(self.)
                    data_result= cmd_api.text_update(string, types, sort_field="num")
                # print data_result
            except Exception, e:
                print e
            s.send(data_result) #加上时间戳返回


class CmdServer(object):
    def __init__(self):
        pass
        # self.cmd_api = CmdMongo(None)

    def start(self):
        t = threading.Thread(target=handle)
        t.start()
        print u'我在%s线程中 ' % threading.current_thread().name #本身是主线程
        print 'waiting for connecting...'
        while True:
            time.sleep(0.01)
            clientSock, addr = tcpSerSock.accept()
            print 'connected from:', addr
            socks.append(clientSock)


if __name__ == '__main__':
    server = CmdServer()
    server.start()
