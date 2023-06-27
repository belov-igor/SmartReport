import os
import subprocess


# Подключение sh скрипта-сборщика данных по подключенным sg устройствам (диски) утилитой smartctl
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SMARTCTL_SH_SCRIPT_PATH = os.path.join(BASE_DIR, '../scripts/smartctl_script.sh')


class SmartCtlReport:
    """
    Класс-обработчик данных, полученных с результата выполнения sh скрипта-сборщика данных
    с подключенных sg устройств (дисков), использующего утилиту smartctl.

    Выходные данные: drives_count - количество дисков, подключенных к серверу;
                    report - итоговый отчет в виде словаря.
    """

    def __init__(self, username, hostname):
        """
        :param username: имя пользователя при подключении к удаленному хосту;
        :param hostname: имя удаленного хоста.
        """
        self.username = username
        self.hostname = hostname
        self.report = dict()
        self.drives_count = 0
        self.smartctl_script_result = None

    def get_smartctl_data(self):
        """
        Подключение к хостам по ssh, получение и обработка отчета smartctl по всем дискам.
        :return полученный в виде текста поток с выполнения в терминале sh-скрипта сборщика
        """
        open_script = subprocess.Popen([f'cat {SMARTCTL_SH_SCRIPT_PATH}'], stdout=subprocess.PIPE,
                                       shell=True)
        ssh_connect = subprocess.Popen([f'ssh {self.username}@{self.hostname}'], stdin=open_script.stdout,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        open_script.stdout.close()
        self.smartctl_script_result = ssh_connect.communicate()[0].decode().split('\n')

    def get_smartctl_report(self):
        """
        Извлечение данных и обработка.
        :return: report - обработанные данные (отчет) с arcconf smartstats в виде словаря:
                {'sgN':{параметр1: величина1, параметр2: величина2, ...}},
                где N - номер диска; требуемые параметры дисков
        """
        power_on_hours, reallocated_sector_ct = '-', '-'
        current_pending, offline_uncorrectable, media_wearout = '-', '-', '-'
        sg_name = str()
        sg_list = list()
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
            if 'wearout' in string.lower():
                media_wearout = int(string.split()[3])
            self.report.update({sg_name: {'Power-On Hours': power_on_hours,
                                          'Reallocated Sectors Count': reallocated_sector_ct,
                                          'Current Pending Sector Count': current_pending,
                                          'Uncorrectable Sectors Count': offline_uncorrectable,
                                          'Media Wearout Indicator': media_wearout}})

    def run(self):
        """
        Запуск обработчика.
        :return: drives_count - количество дисков, подключенных к серверу;
                 report - итоговый отчет в виде словаря
        """
        self.get_smartctl_data()
        self.get_smartctl_report()

        return self.drives_count, self.report
