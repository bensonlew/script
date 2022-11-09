#!/mnt/ilustre/users/sanger-dev/sg-users/liubinxu/work/spacemacs/miniconda2/bin/python
#-*- coding:utf-8 -*-

import sys
import socket
# import threading
# from time import sleep
# from datetime import datetime
import json
import os

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

global now_environ
now_environ = {
    "dirs": {},
    "files": {},
    "cmds": {}
}


# HOST = 'localhost'
# HOST = '192.168.12.101'
HOST = '10.100.203.61'
PORT = 21590
api_socket = socket.socket()
# api_socket.connect((HOST, PORT))

# api_socket.send(search)
# data = socket1.recv(65536)

def search_text(search):
    method, string, types, sort_field = search.split(";")
    search_dict = {
        "method": method,
        "string": string,
        "types": types,
        "sort_field": sort_field
    }
    api_socket.send(json.dumps(search_dict))
    data = api_socket.recv(65536)
    return data

def auto_command(dir_str, cmd_str):
    global now_environ
    # 判断路径
    ''' 插入命令时自动插入
    if dir_str in now_environ["dirs"]:
        now_environ["dirs"][dir_str] += 1
        pass
    else:
        now_environ["dirs"][dir_str] += 1
        update_dir(dir_str, )
    '''

    # 判断文件
    if len(cmd_str.split()) >= 32 or len(cmd_str.split()) < 1:
        pass
    elif cmd_str.split()[0] in ['less', 'cat', 'zcat', 'nano', 'vi', 'vim', 'emacs', 'grep', 'head', 'tail']:
        for f in cmd_str.split()[1:]:
            if f[0] == "~" or "/" in f:
                if f in now_environ["files"]:
                    now_environ["files"][f] += 1
                else:
                    now_environ["files"][f] = 1
                    update_file(dir_str, f)

    # 判断命令
    if cmd_str.split()[0] not in ['history', 'sgf', 'sgc', 'sgd', 'cd', 'which', 'less', 'cat', 'zcat', 'nano', 'vi', 'vim', 'emacs', 'grep', 'pwd', "ls", 'll', 'mkdir', 'rm', 'head', 'tail', '#'] or "|" in cmd_str:
        if cmd_str.startswith("#"):
            pass
        else:
            if cmd_str in now_environ["cmds"]:
                now_environ["cmds"][cmd_str] += 1
            else:
                now_environ["cmds"][cmd_str] = 1
                update_cmd(dir_str, cmd_str)

                '''
                last_cmd = cmd_id
                cmd_id += 1
                cmd_dict[cmds] = {
                    'id': cmd_id,
                    'time': time,
                    'num': 1,
                    'user': user_name,
                    'dirs': set([dir_id]),
                    'pre_cmds': set()
                }
                if dir_path == last_dir:
                    cmd_dict[cmds]['pre_cmds'].add(last_cmd)
                '''

def update_dir(dir_str):
    pass


def update_cmd(dir_str, cmd_str):
    insert_dict = {
        "method": "text_update",
        "types": "cmds",
        "string": cmd_str,
        "dir": dir_str,
        "user": os.environ["USER"],
        "ssh_client": os.environ["SSH_CLIENT"].split()[0],
        "ssh_port": os.environ["SSH_CLIENT"].split()[1]

    }

    api_socket.send(json.dumps(insert_dict))


def update_file(dir_str, file_str):
    insert_dict = {
        "method": "text_update",
        "types": "file",
        "string": file_str,
        "dir": dir_str,
        "user": os.environ["USER"],
        "ssh_client": os.environ["SSH_CLIENT"].split()[0],
        "ssh_port": os.environ["SSH_CLIENT"].split()[1]
    }

    api_socket.send(json.dumps(insert_dict))

# def text_search(types, sort_field, search_txt):


if __name__ == "__main__":

    # print datetime.now()
    method = sys.argv[1]
    try:
        api_socket.connect((HOST, PORT))
        if method == "text_search":
            types = sys.argv[2]
            sort_field = sys.argv[3]
            search_txt = " ".join(sys.argv[4:])
            search = ";".join([method, search_txt, types, sort_field])
            results = search_text(search)
            print results
        elif method == "auto_cmd":
            try:
                api_socket.connect((HOST, PORT))
            except:
                pass

            if len(sys.argv) < 4:
                pass
            else:
                dir_str = sys.argv[2]
                cmd_str = " ".join(sys.argv[3:])
                result = auto_command(dir_str, cmd_str)
    except:
        pass



    '''
    HOST='localhost'
    PORT = 21590
    socket1 = socket.socket()
    socket1.connect((HOST, PORT))
    socket1.send(search)
    data = socket1.recv(65536)
    # print datetime.now()
    print data

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
