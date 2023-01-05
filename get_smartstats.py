# -*- coding: utf-8 -*-
import os
import subprocess
import numpy
import pandas as pd

from config.hosts import SMARTCTL_HOSTS, ADAPTEC_HOSTS

from scripts.send_email import ReportSender
from scripts.smartctl_report import SmartCtlReport
from scripts.adaptec_smart_report import AdaptecSmartReport
from scripts.drives_count_logger import drive_count_logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_COUNT_TMP_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp.txt')
DRIVE_COUNT_TMP_NEW_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp_new.txt')

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


def get_data_frame(data):
    """
    Формирование html-таблицы
    :param data: данные в виде словаря
    :return: данные, сформированные в html-таблицу
    """
    df = pd.DataFrame.from_dict(data=data, orient='index')
    df = df[['Power-On Hours', 'Reallocated Sectors Count',
             'Current Pending Sector Count', 'Uncorrectable Sectors Count']]
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


def adaptec_counter(username, hostname):
    count = 1
    # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
    arcconf_path = 'arcconf'

    # В esxi arcconf в PATH не добавлен, лежит в собственных datavol
    if 'esxi' in hostname:
        arcconf_path = f'/vmfs/volumes/{hostname}_ssdvol/arcconf'

    connect = subprocess.run(
        ["ssh", f"{username}@{hostname}", f"{arcconf_path}", "getversion"],
        stdout=subprocess.PIPE)
    data = connect.stdout.decode().split('\n')
    for string in data:
        if 'controllers found' in string.lower():
            count = int(string.split(':')[-1])
    return count


if __name__ == '__main__':

    host = str()

    try:

        report_table = '<h2>SMART report</h2>\n'

        # Проход по хостам и формирование отчета в виде html-таблицы
        for host, user_name in SMARTCTL_HOSTS.items():
            report_table = report_table + f'<h3>{host}</h3>\n'
            smartctl_report = SmartCtlReport(username=user_name, hostname=host)
            disc_count, report = smartctl_report.run()
            report_table = report_table + f'{drive_count_logger(host=host, drives_count=disc_count, old_path=DRIVE_COUNT_TMP_PATH, new_path=DRIVE_COUNT_TMP_NEW_PATH)}' \
                                          f'{get_data_frame(data=report)}'

        for host, user_name in ADAPTEC_HOSTS.items():
            report_table = report_table + f'<h3>{host}</h3>\n'
            adaptec_count = adaptec_counter(username=user_name, hostname=host)
            for adaptec in range(1, adaptec_count + 1):
                smart_adaptec_report = AdaptecSmartReport(username=user_name, hostname=host, adaptec_num=adaptec)
                disc_count, adaptec_name, report = smart_adaptec_report.run()
                report_table = report_table + f'<div style="font-weight: bold; margin-top: 5px">Adaptec {adaptec_name}\n</div>' \
                                              f'{drive_count_logger(host=host, drives_count=disc_count, adaptec_num=adaptec, old_path=DRIVE_COUNT_TMP_PATH, new_path=DRIVE_COUNT_TMP_NEW_PATH)}' \
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
