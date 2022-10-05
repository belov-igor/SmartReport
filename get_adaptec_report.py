# -*- coding: utf-8 -*-

import subprocess
import pandas as pd
import pretty_html_table

from hosts import HOSTS
from send_email import ReportSender


class SmartReport:

    def __init__(self, hostname):
        self.df = None
        self.table = None
        self.hostname = hostname
        self.config = dict()
        self.device_name = ''
        self.device_status = ''
        self.data = ''

    def logical_device_status(self):
        # host = self.hostname
        connect = subprocess.run(
            ["ssh", f"root@{self.hostname}", "/root/bin/arcconf", "GETCONFIG", "1", "ld"],
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


def get_data_frame(data):
    df = pd.DataFrame.from_dict(data=data, orient='index')
    df.to_html()
    table = pretty_html_table.build_table(df=df, color='blue_light', index=True)
    return table


if __name__ == '__main__':

    with open('hosts.py') as hosts:
        adaptec_report = dict()

        try:
            for host in HOSTS:
                report = SmartReport(hostname=host)
                ld_stat = report.run()
                adaptec_report.update({host: ld_stat})
            report_table = f'<h3>Adaptec report</h3> \n ' \
                           f'{get_data_frame(data=adaptec_report)} '
        except Exception as error:
            report_table = error
        else:
            print(report_table)
            report_message = ReportSender(subject='Adaptec report',
                                          body=report_table)
            report_message.run()
