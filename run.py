import os
import subprocess
import numpy
import pandas as pd


from config.hosts import SMARTCTL_HOSTS, ADAPTEC_HOSTS

from scripts.send_email import ReportSender
from scripts.smartctl_report import SmartCtlReport
from scripts.adaptec_smart_report import AdaptecSmartReport
from scripts.drives_count_logger import drive_count_logger

# Пути к используемым временным файлам-логов количества дисков удаленного хоста
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_COUNT_TMP_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp.txt')
DRIVE_COUNT_TMP_NEW_PATH = os.path.join(BASE_DIR, 'tmp/drive_count_tmp_new.txt')

# Стили, используемые при формировании html-таблицы. Подставляются pandas dataframe как стили СSS
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
    # df = df[['Power-On Hours', 'Reallocated Sectors Count',
    #          'Current Pending Sector Count', 'Uncorrectable Sectors Count',
             # 'Media Wearout Indicator'
             # ]]
    df = df.replace({numpy.nan: '-'})

    table = df.style.set_table_styles(table_styles=TABLE_STYLES). \
        format({'Reallocated Sectors Count':
                    lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x,
                'Current Pending Sector Count':
                    lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x,
                'Uncorrectable Sectors Count':
                    lambda x: f'<p style="background-color:red">{x}</p>' if x != '-' and int(x) > 0 else x}) \
        .render()

    return table


def adaptec_counter(username, hostname):
    """
    Функция подсчета количества используемых adaptec на удаленном хосте

    :param username: имя пользователя при подключении к удаленному хосту;
    :param hostname: имя удаленного хоста;
    :return: количество используемых adaptec
    """
    count = 1
    # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
    arcconf_path = 'arcconf'
    # В esxi arcconf в PATH не добавлен, лежит в собственных datavol или ssdvol (унифицировать, к сожалению, нельзя)
    if 'esxi' in hostname:
        arcconf_path = f'/vmfs/volumes/{hostname}_ssdvol/arcconf'
    # Подключение к хостам по ssh, получение данных arcconf getversion
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

        report_table = '<h1>SMART report</h1>\n'

        # Проход по хостам и формирование отчета в виде html-таблицы для хостов, использующий утилиту smartctl
        for host, user_name in SMARTCTL_HOSTS.items():
            report_table = report_table + f'<h2>{host}</h2>\n'
            # Использования класса-обработчика
            smartctl_report = SmartCtlReport(username=user_name, hostname=host)
            drive_count, report = smartctl_report.run()
            # Обращение к логеру количества дисков для сравнения
            drives_count_compare = drive_count_logger(host=host, drives_count=drive_count,
                                                      old_path=DRIVE_COUNT_TMP_PATH,
                                                      new_path=DRIVE_COUNT_TMP_NEW_PATH)
            # Формирование html-таблицы с результатами
            report_table = f'{report_table} ' \
                           f'{drives_count_compare}' \
                           f'{get_data_frame(data=report)}'

        # Проход по хостам и формирование отчета в виде html-таблицы для хостов, использующий adaptec arcconf
        for host, user_name in ADAPTEC_HOSTS.items():
            report_table = report_table + f'<h2>{host}</h2>\n'
            # Подсчет количества adaptec, используемых на сервере
            adaptec_count = adaptec_counter(username=user_name, hostname=host)
            # Использования класса-обработчика
            for adaptec in range(1, adaptec_count + 1):
                smart_adaptec_report = AdaptecSmartReport(username=user_name, hostname=host, adaptec_num=adaptec)
                drive_count, adaptec_name, report = smart_adaptec_report.run()
                # Обращение к логеру количества дисков для сравнения
                drives_count_compare = drive_count_logger(host=host, drives_count=drive_count, adaptec_num=adaptec,
                                                          old_path=DRIVE_COUNT_TMP_PATH,
                                                          new_path=DRIVE_COUNT_TMP_NEW_PATH)
                # Формирование html-таблицы с результатами
                report_table = f'{report_table} ' \
                               f'<div style="font-weight: bold; margin-top: 5px">Adaptec {adaptec_name}</div>' \
                               f'{drives_count_compare}' \
                               f'{get_data_frame(data=report)}'

    except Exception as error:
        # Запись ошибки для отправки в письме
        report_table = error.args
    else:
        # Замена файла-лога с записью о количестве дисков на актуальный
        os.rename(DRIVE_COUNT_TMP_NEW_PATH, DRIVE_COUNT_TMP_PATH)

        # Отправка отчета
        report_message = ReportSender(subject='SMART report',
                                      body=report_table)
        report_message.run()
