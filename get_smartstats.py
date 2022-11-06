# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ETree
import pandas as pd
import pretty_html_table
import copy

from info.hosts import WINDOWS_HOSTS, LINUX_HOSTS  # хосты из файла, разделены на списки windows и linux
from send_email import ReportSender

PARAMS = {
    '0x09': 'Power-On Hours',
    '0x05': 'Reallocated Sectors Count',
    '0xC5': 'Current Pending Sector Count',
    '0xC6': 'Uncorrectable Sectors Count'
}


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
        connect = subprocess.run(
            ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", "1"],
            stdout=subprocess.PIPE)
        self.smarts_data = connect.stdout.decode().split('\n')
        for string in self.smarts_data:
            if '<SmartStats' in string:
                self.min_string = self.smarts_data.index(string)
            if '</SmartStats>' in string:
                self.max_string = self.smarts_data.index(string) + 1
        with open('/tmp/smartstats_temp.xml', 'w') as smartstats_xml:
            xml = '\n'.join(self.smarts_data[self.min_string:self.max_string]) + '\n'
            smartstats_xml.write(xml)
        # smartstats_xml.close()

    def get_adaptec_smart_report(self):
        self.drives = []
        stats = ETree.parse('/tmp/smartstats_temp.xml')
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
                    # print(param_id)
                    param_name = PARAMS[param_id]
                    param_value = int(drives_attrib.attrib["rawValue"])
                    self.config1.update({param_name: param_value})
            self.config.update({f'id={drive}': copy.deepcopy(self.config1)})

    def get_disks(self):
        """
        :return
        """
        pass

    def smartctl_report(self):
        """

        :return:
        """
        # Подключение к хостам по ssh, получение данных smartctl
        # connect = subprocess.run(
        #     ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", "1"],
        #     stdout=subprocess.PIPE)
        # # self.smarts_data = connect.stdout.decode().split('\n')
        # with open('smartctl_out.txt', 'r') as stats:
        #     for string in stats:
        #         if 'power_on_hours' in string.lower():
        #             power_on_hours = string.split()[-1]
        #         if 'reallocated' in string.lower():
        #             reallocated_sector_ct = string.split()[-1]
        #         if 'current_pending' in string.lower():
        #             current_pending = string.split()[-1]
        #         if 'offline_uncorrectable' in string.lower():
        #             offline_uncorrectable = string.split()[-1]

    def run(self):
        # self.get_adaptec_smarts_data()
        self.get_adaptec_smart_report()
        return self.config


def get_data_frame(data):
    """
    Формирование html-таблицы
    :param data: данные в виде словаря
    :return: данные, сформированные в html-таблицу
    """
    styles = [
        dict(selector="tr:hover",
             props=[("background", "#f4f4f4")]),
        dict(selector="th", props=[("color", "black"),
                                   ("border", "0 solid #305496"),
                                   ("padding", "0 5px"),
                                   ("font-family", 'sans-serif'),
                                   ("border-collapse", "collapse"),
                                   ("background", "#D9E1F2"),
                                   ("font-size", "14px")
                                   ]),
        dict(selector="td", props=[("color", "black"),
                                   ("font-family", 'sans-serif'),
                                   ("border", "0.5px solid #eee"),
                                   ("padding", "0px 0px"),
                                   ("text-align", "center"),
                                   ("border-collapse", "collapse"),
                                   ("font-size", "14px")
                                   ]),
    ]
    df = pd.DataFrame.from_dict(data=data, orient='index')

    table = df.style.set_table_styles(table_styles=styles).format(
        {'Reallocated Sectors Count': lambda x: f'<p style="background-color:red">{x}</p>' if int(x) > 0 else x},
        {'Current Pending Sector Count': lambda x: f'<p style="background-color:red">{x}</p>' if int(x) > 0 else x},
        {'Uncorrectable Sectors Count': lambda x: f'<p style="background-color:red">{x}</p>' if int(x) > 0 else x}
    ).render()

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
                ld_stat = report.run()
                adaptec_report.update({host: ld_stat})
                report_table = report_table + f'<h3>{host}</h3>\n' \
                                              f'{get_data_frame(data=ld_stat)}'
    except Exception as error:
        report_table = error
        print(error)
    else:
        # Отправка отчета
        # TODO need done sending error with mail
        with open('test.html', 'w') as html:
            html.write(report_table)
    #     report_message = ReportSender(subject='SMART report',
    #                                   body=report_table)
    #     report_message.run()
