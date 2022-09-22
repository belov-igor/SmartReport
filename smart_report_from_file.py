# -*- coding: utf-8 -*-

import paramiko
import os


class SmartReport:

    def __init__(self, hostname, rsa_key=os.path.expanduser("~/.ssh/id_rsa")):
        self.config = dict()
        self.device_name = ''
        self.device_status = ''
        self.client = paramiko.SSHClient()
        self.hosthame = hostname
        self.rsa_key = rsa_key
        self.data = ''

    # def connect(self):
    #     key = paramiko.RSAKey.from_private_key_file(self.rsa_key)
    #     self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    #     self.client.connect(hostname=self.hosthame, username='root', pkey=key)

    def logical_device_status(self):
        stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETCONFIG 1 ld')
        self.data = stdout.read().decode().split('\n')
        for string in self.data:
            if 'device name' in string:
                self.device_name = string.split()[-1]
            elif 'Status of logical device' in string:
                self.device_status = string.split()[-1]
        self.config = {self.device_name: self.device_status}
        self.data = stdout.read().decode()

    def physical_device_status(self):
        stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETCONFIG 1 pd')
        report = stdout.read().decode()

    def smart_stats(self):
        stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETSMARTSTATS 1')
        # print(stdout.read().decode())
        # stdin, stdout, stderr = client.exec_command('/root/bin/arcconf getlogs 1 uart')

    def run(self):
        self.connect()
        self.logical_device_status()
        # self.physical_device_status()
        # self.smart_stats()
        self.client.close()
        return self.config


# if __name__ == '__main__':

    # with open('hosts.txt') as hosts:
    #     adaptec_report = dict()
    #
    #     try:
    #         for line in hosts:
    #             host = line[:-1]
    #             report = SmartReport(hostname=host)
    #             ld_stat = report.run()
    #             adaptec_report.update({host: ld_stat})
    #         data = f'Adaptec report: \n ' \
    #                f'{adaptec_report} '
    #     except Exception as error:
    #         data = error
    #
    #     print(data)

if __name__ == '__main__':

    try:
        # getconfig = '/root/bin/arcconf GETCONFIG 1 ld'
        # os.system(getconfig)

        getconfig = os.popen('/root/bin/arcconf GETCONFIG 1 ld').read()
        print(getconfig)

        ls = os.popen('ls -l').read()
        print(ls)
    except Exception as error:
        print('Error')
