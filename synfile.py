# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import os
import re
import sys
import paramiko
import difflib
import subprocess
import socket, fcntl, struct

class Syn(object):
    def __init__(self, to_host):
        '''
        初始化环境， 设置ssh key所在路径
        '''
        self.key_dir = os.getenv('SSH_KEYS_DIR')
        self.key_base_name = dict({
            "tsg": "tsg_id_rsa",
            "tsanger": "tsanger_id_rsa",
            "sanger": "sanger_id_rsa",
            "rocks7": "rocks_id_rsa",
            "nb": "nb_id_rsa"
        })
        self.user_ip = dict({
            "tsg": "192.168.12.102",
            "tsanger": "192.168.12.102",
            "sanger": "192.168.12.102",
            "rocks7": "192.168.12.16",
            "nb": "10.2.0.110"
        })
        self.user_dir = dict({
            "tsg": "sanger-dev",
            "tsanger": "sanger-test",
            "sanger": "sanger",
            "rocks7": "rocks7",
            "nb": "sanger"
        })
        self.bio_dir = dict({
            "tsg": "biocluster",
            "tsanger": "biocluster",
            "sanger": "sanger_bioinfo",
            "rocks7": "biocluster",
            "nb": "sanger_bioinfo"
        })
        self.lustre_dir = dict({
            "tsg": "ilustre",
            "tsanger": "ilustre",
            "sanger": "ilustre",
            "rocks7": "ilustre",
            "nb": "lustre"
        })

        self.user = self.get_user()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.user_ip[self.user], username=self.user, key_filename = os.path.join(self.key_dir, self.key_base_name[to_host]))

    def get_user(self):
        if os.getenv('USER') == "sanger-dev":
            return "tsg"
        elif os.getenv('USER') == "sanger-test":
            return "tsanger"
        elif os.getenv('USER') == "sanger":
            ip = ""
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ip = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(), 0x8915, struct.pack('256s', "eth1"))[20:24])
            except:
                pass

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ip = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(), 0x8915, struct.pack('256s', "ens192"))[20:24])
            except:
                pass
            if ip == "10.2.0.110":
                return "nb"
            elif ip in ["192.168.10.102", "192.168.10.101"]:
                return "sanger"
            elif ip == "192.168.12.16":
                return "rocks7"
        else:
            return "other"

    def get_to_path(self, from_path, to_user):
        '''
        获取目标文件路径
        '''
        to_path = from_path.replace(self.user_dir[self.user], self.user_dir[to_user], 1)
        to_path = to_path.replace(self.bio_dir[self.user], self.bio_dir[to_user], 1)
        to_path = to_path.replace(self.lustre_dir[self.user], self.lustre_dir[to_user], 1)
        return to_path

    def get_real_path(self, from_path):
        '''
        获取绝对路径
        '''
        if from_path.statswith("~/"):
            from_path = from_path.replace("~", os.getenv("HOME"), 1)
        else:
            from_path = os.path.abspath(from_path)
        return from_path

    def diff_file(self, user, from_file, diff=True):
        '''
        判断文件是否和本地相同, 并返回差异结果
        '''
        tail = from_file.split(".")[-1]
        to_file = self.get_to_path(from_file, user)
        if self.md5_compare(from_file, to_file):
            pass
        elif diff:
            pass
        elif os.path.getsize(from_file) > 100000:
            pass
        elif tail in ['png', 'pdf', 'so', 'a', 'zip', 'gz']:
            pass
        else:
            stdin, stdout, stderr = self.client.exec_command('cat {}'.format(to_file))
            with open(from_file, 'r') as from_f:
                from_lines = [line.rstrip() for line in from_f.readlines()]
            to_lines = [line.rstrip() for line in stdout]
            d = difflib.Differ()
            diff = d.compare(from_lines, to_lines)
            print('\n'.join(list(diff)))

    def diff_dir(self, user, from_dir):
        '''
        判断文件是否和本地相同, 并返回差异结果
        '''
        for base,dir_path,file_path in os.walk(from_dir):
            to_base = self.get_to_path(base, user)
            self.client.exec_command('mkdir -p {}'.format(to_base))
            for file_1 in file_path:
                self.diff_file(to_user, base + "/" + file_1, diff=True)


    def md5_compare(self, from_file, to_file):
        '''
        判断大文件 md5是否相同
        '''
        stdin, stdout, stderr = self.client.exec_command('md5sum {}'.format(to_file))
        to_md5 = stdout.split()[0]

        p = subprocess.Popen("md5sum {}".format(from_file), stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        from_md5 = output.split()[0]

        if to_md5 == from_md5:
            print "{} 与远程相同".format(from_file)
            return True
        else:
            print "{} 与远程不同 本地为 {} 远程为 {}".format(from_file, from_md5, to_md5)
            return False

    def to_file(self, to_user, from_file, to_file=None):
        '''
        上传单个文件
        '''
        to_file = self.get_to_path(from_file, to_user)
        file_size = os.path.getsize(from_file)
        if self.md5_compare(from_file, to_file):
            print "{} 与远程文件相同跳过上传"
            return
        else:
            os.system("scp -i {} {} {}@{}:{}").format(
                os.path.join(self.key_dir, self.key_base_name[to_user]),
                from_file,
                to_user,
                self.user_ip[to_user],
                to_file
            )
            return

        file_tail = from_file.split(".")[-1]

    def to_dir(self, to_user, from_dir):
        '''
        同步目录
        '''
        for base,dir_path,file_path in os.walk(from_dir):
            to_base = self.get_to_path(base, to_user)
            self.client.exec_command('mkdir -p {}'.format(to_base))
            for file_1 in file_path:
                self.to_file(to_user, base + "/" + file_1)

    def get_file(self, to_user, to_path):
        '''
        获取文件，到当前目录
        '''
        if not to_path.startswith("/"):
            raise Exception("{} 需要为绝对路径".format(to_path))
        else:
            os.system("scp -i -r {} {}@{}:{}").format(
                os.path.join(self.key_dir, self.key_base_name[to_user]),
                to_user,
                self.user_ip[to_user],
                to_path,
                "./" + os.path.basename(to_path)
            )

if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise Exception("""
        python synfile.py to|get|diff sanger|tsg|tsanger|rocks7|nb files
        to : 上传文件到远程服务器
        get : 自远程
        """ + "\n")

    to_user = sys.argv[2]
    syn = Syn(to_user)
    if syn.user == sys.argv[2]:
        raise Exception("现在在 {} 不需要同步文件".format(syn.user))

    for path in sys.argv[3:]:
        path = syn.get_real_path(path)
        if syn.user == "tsg" and to_user == "tsanger" and path.startswith("/mnt/ilustre/users/sanger-dev/app"):
            print "app 目录文件自动同步跳过"
            continue
        if sys.argv[1] == "to":
            if os.path.exists(path):
                if os.path.isdir(path):
                    syn.to_dir(to_user, path)
                else:
                    syn.to_file(to_user, path)
            else:
                raise Exception("文件不存在 {}".format(path))
        elif sys.argv[1] == "from":
            if os.path.exists(path):
                syn.get_file(to_user, path)
        elif sys.argv[1] == "diff":
            if os.path.exists(path):
                if os.path.isdir(path):
                    syn.diff_dir(to_user, path)
                else:
                    syn.diff_file(to_user, path)
            else:
                raise Exception("文件不存在 {}".format(path))
        else:
            raise Exception("只可以执行以下操作 {}".format("to|get|diff"))
