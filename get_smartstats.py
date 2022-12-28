# -*- coding: utf-8 -*-

import copy
import subprocess
import os
import xml.etree.ElementTree as ETree

import numpy
import pandas as pd
from datetime import date

from config.hosts import SMARTCTL_HOSTS, ADAPTEC_HOSTS
from send_email import ReportSender

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_COUNT_TMP_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp.txt')
DRIVE_COUNT_TMP_NEW_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp.txt')

DISC_PARAMETERS = {
    '0x05': 'Reallocated Sectors Count',
    '0x09': 'Power-On Hours',
    '0xC5': 'Current Pending Sector Count',
    '0xC6': 'Uncorrectable Sectors Count'
}

TABLE_STYLES = [
    dict(selector="tr:hover",
         props=[
             ("background", "#f4f4f4")]),
    dict(selector="th",
         props=[
             ("color", "black"),
             ("border", "0 solid #305496"),
             ("padding", "0 5px"),
             ("font-family", 'sans-serif'),
             ("border-collapse", "collapse"),
             ("background", "#D9E1F2"),
             ("font-size", "14px")
         ]),
    dict(selector="td",
         props=[
             ("color", "black"),
             ("font-family", 'sans-serif'),
             ("border", "0.5px solid #eee"),
             ("padding", "0 0"),
             ("text-align", "center"),
             ("border-collapse", "collapse"),
             ("font-size", "14px")
         ]),
]


class SmartCtlReport:

    def __init__(self, username, hostname):
        self.username = username
        self.hostname = hostname
        self.report = dict()
        self.drives_count = 0
        self.smartctl_script_result = None

    def get_smartctl_data(self):
        """
        :return
        """
        open_script = subprocess.Popen(['cat /root/bin/smartctl_script.sh'], stdout=subprocess.PIPE, shell=True)
        ssh_connect = subprocess.Popen([f'ssh {self.username}@{self.hostname}'], stdin=open_script.stdout,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        open_script.stdout.close()
        self.smartctl_script_result = ssh_connect.communicate()[0].decode().split('\n')

    def get_smartctl_report(self):
        """

        :return:
        """
        power_on_hours, reallocated_sector_ct, current_pending, offline_uncorrectable = '-', '-', '-', '-'
        sg_name = ''
        sg_list = []
        for string in self.smartctl_script_result:
            if "/dev/" in string.lower():
                sg_name = string[5:]
                sg_list.append(sg_name)
                self.drives_count = len(sg_list)
            if 'reallocated' in string.lower():
                reallocated_sector_ct = int(string.split()[-1])
            if 'power_on_hours' in string.lower():
                power_on_hours = int(string.split()[9])
            if 'current_pending' in string.lower():
                current_pending = int(string.split()[-1])
            if 'offline_uncorrectable' in string.lower():
                offline_uncorrectable = int(string.split()[-1])
            self.report.update({sg_name: {'Reallocated Sectors Count': reallocated_sector_ct,
                                          'Power-On Hours': power_on_hours,
                                          'Current Pending Sector Count': current_pending,
                                          'Uncorrectable Sectors Count': offline_uncorrectable}})

    def run(self):
        #
        self.get_smartctl_data()
        self.get_smartctl_report()

        return self.drives_count, self.report


class AdaptecSmartReport:

    def __init__(self, username, hostname):
        self.username = username
        self.hostname = hostname
        self.report = dict()
        self.drives_count = 0
        self.min_string = 0
        self.max_string = 0
        self.adaptec_smart_data = None
        self.config1 = {}  # TODO rename

    def get_adaptec_smarts_data(self):
        """
        Подключение к хостам по ssh, получение и обработка отчета adaptec arcconf по логическим дискам.
        :return: сonfig - обработанные данные с arcconf smartstats в виде словаря.
        """
        # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
        arcconf_path = 'arcconf'

        # В esxi arcconf в PATH не добавлен, лежит в собственных datavol
        if 'esxi' in self.hostname:
            arcconf_path = f'/vmfs/volumes/{self.hostname}_ssdvol/arcconf'

        # Подключение к хостам по ssh, получение данных arcconf smartstats
        connect = subprocess.run(
            ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", "1"],
            stdout=subprocess.PIPE)
        self.adaptec_smart_data = connect.stdout.decode().split('\n')
        for string in self.adaptec_smart_data:
            if '<SmartStats' in string:
                self.min_string = self.adaptec_smart_data.index(string)
            if '</SmartStats>' in string:
                self.max_string = self.adaptec_smart_data.index(string) + 1
        with open('/tmp/smartstats_temp.xml', 'w') as smartstats_xml:
            xml = '\n'.join(self.adaptec_smart_data[self.min_string:self.max_string]) + '\n'
            smartstats_xml.write(xml)

    def get_adaptec_smart_report(self):
        """

        :return:
        """
        drives = []
        stats = ETree.parse('/tmp/smartstats_temp.xml')
        # Найти корень
        root = stats.getroot()
        for physical_drives in root:
            drive = physical_drives.attrib['id']
            drives.append(physical_drives.attrib['id'])
            self.config1 = {}
            for drives_attrib in physical_drives:
                param_id = drives_attrib.attrib['id']
                if param_id in DISC_PARAMETERS:
                    param_name = DISC_PARAMETERS[param_id]
                    param_value = drives_attrib.attrib["rawValue"]
                    self.config1.update({param_name: param_value})
                self.report.update({f'id={drive}': copy.deepcopy(self.config1)})
            self.drives_count = len(drives)

    def run(self):

        #
        self.get_adaptec_smarts_data()
        self.get_adaptec_smart_report()
        #
        os.remove('/tmp/smartstats_temp.xml')

        return self.drives_count, self.report


def drive_count(host, drive_count):
    old_date = ''
    disc_count_old = ''
    with open(DRIVE_COUNT_TMP_PATH, 'r') as drive_count_log_old:
        for line in drive_count_log_old:
            if host in line.split():
                old_date = line.split()[1]
                disc_count_old = line.split()[2]
    with open(DRIVE_COUNT_TMP_NEW_PATH, 'a') as drive_count_log_new:
        new_date = date.today().strftime("%d.%m.%Y")
        drive_count_log_new.write(f'{host} {new_date} {drive_count}\n')
    return f'Всего дисков на сегодня ({new_date}) - <b>{drive_count}</b>. ' \
           f'Дисков при прошлой проверке ({old_date}) - <b>{disc_count_old}</b>.'


def get_data_frame(data):
    """
    Формирование html-таблицы
    :param data: данные в виде словаря
    :return: данные, сформированные в html-таблицу
    """
    df = pd.DataFrame.from_dict(data=data, orient='index')
    df = df.replace({numpy.nan: '-'})
    table = df.style.set_table_styles(table_styles=TABLE_STYLES). \
        format(
        {'Reallocated Sectors Count':
            lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x,
         'Current Pending Sector Count':
            lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x,
         'Uncorrectable Sectors Count':
            lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x
         },
    ).render()

    return table


if __name__ == '__main__':

    host = str()

    try:

        report_table = '<h2>SMART report</h2>\n'

        # Проход по хостам и формирование отчета в виде html-таблицы
        for host, user_name in SMARTCTL_HOSTS.items():
            smartctl_report = SmartCtlReport(username=user_name, hostname=host)
            disc_count, report = smartctl_report.run()
            report_table = report_table + f'<h3>{host}</h3>\n' \
                                          f'{drive_count(host=host, drive_count=disc_count)}' \
                                          f'{get_data_frame(data=report)}'

        for host, user_name in ADAPTEC_HOSTS.items():
            smart_adaptec_report = AdaptecSmartReport(username=user_name, hostname=host)
            disc_count, report = smart_adaptec_report.run()
            report_table = report_table + f'<h3>{host}</h3>\n' \
                                          f'{drive_count(host=host, drive_count=disc_count)}' \
                                          f'{get_data_frame(data=report)}'

    except Exception as error:
        report_table = error
        print(f'{host}: {error}')
    else:
        os.rename(DRIVE_COUNT_TMP_NEW_PATH, DRIVE_COUNT_TMP_PATH)

        # Отправка отчета
        # TODO need done sending error with mail
        report_message = ReportSender(subject='SMART report',
                                      body=report_table)
        report_message.run()
