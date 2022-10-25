# -*- coding: utf-8 -*-

import subprocess
import pandas as pd
import pretty_html_table

from info.hosts import WINDOWS_HOSTS, LINUX_HOSTS
from send_email import ReportSender


class SmartReport:

    def __init__(self, username, hostname):
        self.df = None
        self.table = None
        self.username = username
        self.hostname = hostname
        self.config = dict()
        self.device_name = ''
        self.device_status = ''
        self.data = ''

    def logical_device_status(self):
        arcconf_path = 'arcconf'
        if 'esxi' in self.hostname:
            arcconf_path = f'/vmfs/volumes/{self.hostname}_datavol/arcconf'
        connect = subprocess.run(
            ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETCONFIG", "1", "ld"],
            stdout=subprocess.PIPE)
        self.data = connect.stdout.decode().split('\n')
        for string in self.data:
            if 'device name' in string.lower():
                self.device_name = string.split()[-1]
            if 'status of logical device' in string.lower():
                self.device_status = string.split()[-1]
            self.config.update({self.device_name: self.device_status})

    def run(self):
        self.logical_device_status()
        return self.config


def get_data_frame(data):
    df = pd.DataFrame.from_dict(data=data, orient='index')
    df.to_html()
    table = pretty_html_table.build_table(df=df, color='blue_light', index=True,
                                          text_align='center', padding="0px 5px 0px 5px")
    return table


if __name__ == '__main__':

    adaptec_report = dict()
    hosts = dict()

    try:
        #
        windows_hosts = [host for host in WINDOWS_HOSTS]
        linux_hosts = [host for host in LINUX_HOSTS]
        hosts.update({'root': linux_hosts,
                      'Administrator': windows_hosts})

        for user_name, host in hosts.items():
            for hostname in host:
                report = SmartReport(username=user_name, hostname=hostname)
                ld_stat = report.run()
                adaptec_report.update({hostname: ld_stat})
        report_table = f'<h3>Adaptec report</h3>\n'\
                       f'{get_data_frame(data=adaptec_report)}'
    except Exception as error:
        report_table = error
    else:
        # print(report_table)
        report_message = ReportSender(subject='Adaptec report',
                                      body=report_table)
        report_message.run()
