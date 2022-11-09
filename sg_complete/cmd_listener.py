# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

# from cmd_mongo_api import CmdMongo
from cmd_api import ApiBase
from socket import *
from time import ctime
import logging
import threading
import time
import json
import os
import sys

HOST=''
PORT=21590
BUFSIZ=4096
ADDR = (HOST,PORT)

tcpSerSock=socket(AF_INET,SOCK_STREAM)
tcpSerSock.bind(ADDR)
tcpSerSock.listen(5)
socks=[]

# cmd_api = CmdMongo(None)
# cmd_api = ApiBase(None)
logpath = "cmd_log.txt"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(logpath, mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s   %(filename)s   %(levelname)s : %(message)s"))
cmd_api = ApiBase(bind_object=logger)
logger.addHandler(file_handler)

def handle():
    while True:
        time.sleep(0.01)
        for s in socks:
            try:
                data = s.recv(BUFSIZ)
            except Exception, e:
                continue
            if not data:
                # s.close()
                socks.remove(s)
                continue
            data_result = "no return"

            try:
                logger.info("recived {}".format(data))
                data_dict = json.loads(data)

                if data_dict["method"] == "text_search":
                    # [method,string,types,sort_field] = data_dict.split(";")
                    # print data_dict
                    data_result= cmd_api.text_search(data_dict["string"], data_dict["types"], sort_field=data_dict["sort_field"])

                if data_dict["method"] == "text_update":
                    # [method,string,dir,num] = data_dict.split(";")
                    # print data_dict
                    if data_dict['types'] == "cmds":
                        logger.info("insert cmds")
                        dir_id = cmd_api.dir_update(data_dict['dir'])
                        logger.info(dir_id)
                        re_id = cmd_api.cmd_update(data_dict['string'], dirs=[dir_id], user=data_dict["user"], ssh_client=data_dict["ssh_client"], ssh_port=data_dict["ssh_port"])

                    elif data_dict['types'] == "file":
                        dir_id = cmd_api.dir_update(data_dict['dir'])
                        re_id = cmd_api.file_update(data_dict['string'], dirs=[dir_id], ssh_client=data_dict["ssh_client"], ssh_port=data_dict["ssh_port"])
                    data_result = str(re_id)

            except Exception as e:
                logger.info(e)
            if data_result:
                s.send(data_result.encode('utf-8'))
            else:
                s.send("not_find")
            s.close()



class CmdServer(object):
    def __init__(self):
        pass
        # self.cmd_api = CmdMongo(None)

    def start(self):
        t = threading.Thread(target=handle)
        t.start()
        # print u'我在%s线程中 ' % threading.current_thread().name #本身是主线程
        print 'waiting for connecting...'
        while True:
            time.sleep(0.01)
            clientSock, addr = tcpSerSock.accept()
            logger.info('connected from:{}'.format(addr))
            # print 'connected from:', addr
            socks.append(clientSock)


if __name__ == '__main__':
    server = CmdServer()
    server.start()
