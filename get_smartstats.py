# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ETree
import pandas as pd
import pretty_html_table
import copy

from info.hosts import WINDOWS_HOSTS, LINUX_HOSTS  # хосты из файла, разделены на списки windows и linux
from send_email import ReportSender

PARAMS = ['0x09', '0x05', '0xC5', '0xC6']


class SmartReport:

    def __init__(self, username, hostname):
        self.config1 = {}
        self.drives = []
        self.df = None
        self.table = None
        self.username = username
        self.hostname = hostname
        self.config = dict()
        self.min_string = 0
        self.max_string = 0
        # self.device_name = ''
        # self.device_status = ''
        self.smarts_data = ''

    def get_adaptec_smarts_data(self):
        """
        Подключение к хостам по ssh, получение и обработка отчета adaptec arcconf по логическим дискам.
        :return: сonfig - обработанные данные с arcconf smartstats в виде словаря.
        """
        # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
        arcconf_path = 'arcconf'

        # В esxi arcconf в PATH не добавлен, лежит в собственных datavol
        if 'esxi' in self.hostname:
            arcconf_path = f'/vmfs/volumes/{self.hostname}_datavol/arcconf'

        # Подключение к хостам по ssh, получение данных arcconf smartstats
        # connect = subprocess.run(
        #     ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", "1"],
        #     stdout=subprocess.PIPE)
        # self.smarts_data = connect.stdout.decode().split('\n')
        # for string in self.smarts_data:
        #     if '<SmartStats' in string:
        #         self.min_string = self.smarts_data.index(string)
        #     if '</SmartStats>' in string:
        #         self.max_string = self.smarts_data.index(string) + 1
        # smartstats_xml = open('smartstats_temp.xml', 'w')
        # xml = '\n'.join(self.smarts_data[self.min_string:self.max_string]) + '\n'
        # smartstats_xml.write(xml)
        # smartstats_xml.close()

    def get_adaptec_smart_report(self):
        self.drives = []
        stats = ETree.parse('smartstats_temp.xml')
        # Найти корень
        root = stats.getroot()
        for root_attrib in root.attrib:
            if 'devicename' in root_attrib.lower():
                device_name = root.attrib[root_attrib]
        for physical_drives in root:
            drive = physical_drives.attrib['id']
            self.drives.append(physical_drives.attrib['id'])
            for drives_attrib in physical_drives:
                param_id = drives_attrib.attrib['id']
                if param_id in PARAMS:
                    param_name = drives_attrib.attrib["name"]
                    param_value = drives_attrib.attrib["rawValue"]
                    self.config1.update({param_name: param_value})
            self.config.update({drive: copy.deepcopy(self.config1)})

        # for string in self.smarts_data:
        #     if 'device name' in string.lower():
        #         self.device_name = string.split()[-1]
        #     if 'status of logical device' in string.lower():
        #         self.device_status = string.split()[-1]
        #     self.config.update({self.device_name: self.device_status})

    def run(self):
        self.get_adaptec_smarts_data()
        self.get_adaptec_smart_report()
        return self.drives, self.config


def get_data_frame(data):
    """
    Формирование html-таблицы
    :param data: данные в виде словаря
    :return: данные, сформированные в html-таблицу
    """
    df = pd.DataFrame.from_dict(data=data, orient='columns')
    df.to_html()
    table = pretty_html_table.build_table(df=df, color='grey_light', index=True,
                                          text_align='left', padding="0px 5px 0px 5px")
    return table


if __name__ == '__main__':

    adaptec_report = dict()
    hosts_dict = dict()

    try:
        # Формирование словаря со списком хостов, где ключ - имя пользователя
        hosts_dict.update({'root': LINUX_HOSTS,
                           'Administrator': WINDOWS_HOSTS})

        report_table = '<h2>SMART report</h2>\n'

        # Проход по хостам и формирование отчета в виде html-таблицы
        for user_name, hosts in hosts_dict.items():
            for host in hosts:
                report = SmartReport(username=user_name, hostname=host)
                drives, ld_stat = report.run()
                # adaptec_report.update({host: ld_stat})
                # report_table = report_table + f'<h3>{host}</h3>\n' \
                #                               f'{get_data_frame(data=ld_stat)}'
                print(ld_stat)
    except Exception as error:
        report_table = error
        print(error)
    # else:
        # Отправка отчета
        # TODO need done sending error with mail
        # report_message = ReportSender(subject='SMART report',
        #                               body=report_table)
        # report_message.run()
