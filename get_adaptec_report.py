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

    def run(self):
        self.logical_device_status()
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
