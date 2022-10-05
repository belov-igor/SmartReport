# -*- coding: utf-8 -*-

import subprocess
from hosts import HOSTS


class SmartReport:

    def __init__(self, hostname):
        self.hostname = hostname
        self.config = dict()
        self.device_name = ''
        self.device_status = ''
        self.data = ''

    def logical_device_status(self):
        host = self.hostname
        connect = subprocess.run(
            ["ssh", f"root@{host}", "/root/bin/arcconf", "GETCONFIG", "1", "ld"],
            stdout=subprocess.PIPE)
        self.data = connect.stdout.decode().split('\n')
        for string in self.data:
            if 'device name' in string:
                self.device_name = string.split()[-1]
            elif 'Status of logical device' in string:
                self.device_status = string.split()[-1]
        self.config = {self.device_name: self.device_status}

        # stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETCONFIG 1 ld')
        # self.data = stdout.read().decode().split('\n')
        # for string in self.data:
        #     if 'device name' in string:
        #         self.device_name = string.split()[-1]
        #     elif 'Status of logical device' in string:
        #         self.device_status = string.split()[-1]
        # self.config = {self.device_name: self.device_status}
        # self.data = stdout.read().decode()

    # def physical_device_status(self):
        # stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETCONFIG 1 pd')
        # report = stdout.read().decode()

    # def smart_stats(self):
        # stdin, stdout, stderr = self.client.exec_command('/root/bin/arcconf GETSMARTSTATS 1')
        # print(stdout.read().decode())
        # stdin, stdout, stderr = client.exec_command('/root/bin/arcconf getlogs 1 uart')

    def run(self):
        self.logical_device_status()
        # self.physical_device_status()
        # self.smart_stats()
        return self.config


if __name__ == '__main__':

    with open('hosts.py') as hosts:
        adaptec_report = dict()

        try:
            for line in HOSTS:
                # host = line[:-1]
                host = line
                report = SmartReport(hostname=host)
                ld_stat = report.run()
                adaptec_report.update({host: ld_stat})
            data = f'Adaptec report: \n ' \
                   f'{adaptec_report} '
        except Exception as error:
            data = error

        print(data)
