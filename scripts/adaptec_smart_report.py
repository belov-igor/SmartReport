import copy
import os
import subprocess
import xml.etree.ElementTree as ETree

# Путь временного xml-файла (нужен для обработки данных с adaptec, удаляется после выполнения программы)
TMP_XML_PATH = '/tmp/smartstats_temp.xml'

# Требуемые параметры дисков
DRIVE_PARAMETERS = {
    '0x05': 'Reallocated Sectors Count',
    '0x09': 'Power-On Hours',
    '0xC5': 'Current Pending Sector Count',
    '0xC6': 'Uncorrectable Sectors Count',
    '0xE9': 'Media Wearout Indicator',
}


def sort_by_id(item):
    """Return numerical room given a (name, room_number) tuple."""
    name, room = item
    _, number = room.split()
    print(number)
    return int(number)


class AdaptecSmartReport:
    """
    Класс-обработчик данных, полученных с adaptec для подключенных дисков командой arcconf getsmartstats
    Выходные данные: drives_count - количество дисков, подключенных к adaptec;
                    adaptec_name - имя adaptec;
                    report - итоговый отчет в виде словаря.
    """

    def __init__(self, username, hostname, adaptec_num=1):
        """
        :param username: имя пользователя при подключении к удаленному хосту
        :param hostname: имя удаленного хоста
        :param adaptec_num: порядковый номер adaptec (если подключено больше 1-го)
        """
        self.username = username
        self.hostname = hostname
        self.adaptec_num = adaptec_num
        self.report = dict()
        self.drives_count = 0
        self.min_string = 0
        self.max_string = 0
        self.adaptec_name = str()
        self.s_n = str()
        self.adaptec_smart_data = None
        self.one_drive_report = dict()

    def get_adaptec_smart_data(self):
        """
        Подключение к хостам по ssh, получение и обработка отчета adaptec arcconf getsmartstats по всем дискам.
        :return: отчет arcconf getsmartstats xml-файл
        """
        # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
        arcconf_path = 'arcconf'

        # В esxi arcconf в PATH не добавлен, лежит в собственных datavol или ssdvol (унифицировать, к сожалению, нельзя)
        if 'esxi' in self.hostname:
            arcconf_path = f'/vmfs/volumes/{self.hostname}_ssdvol/arcconf'

        # Подключение к хостам по ssh, получение данных arcconf smartstats
        connect = subprocess.run(
            ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", f"{self.adaptec_num}"],
            stdout=subprocess.PIPE)
        self.adaptec_smart_data = connect.stdout.decode().split('\n')
        for string in self.adaptec_smart_data:
            if '<SmartStats' in string:
                self.min_string = self.adaptec_smart_data.index(string)
            if '</SmartStats>' in string:
                self.max_string = self.adaptec_smart_data.index(string) + 1
        with open(TMP_XML_PATH, 'w') as smartstats_xml:
            xml = '\n'.join(self.adaptec_smart_data[self.min_string:self.max_string]) + '\n'
            smartstats_xml.write(xml)

    def get_adaptec_smart_report(self):
        """
        Извлечение данных из xml-файла и их обработка.
        :return: report - обработанные данные (отчет) с arcconf smartstats в виде словаря:
                {'id=N':{параметр1: величина1, параметр2: величина2, ...}},
                где N - номер диска; параметры взяты из константы DRIVE_PARAMETERS
        """
        drives = []

        # Открытие xml-файла библиотекой Etree
        stats = ETree.parse(TMP_XML_PATH)

        # Найти корень xml-файла
        root = stats.getroot()

        # Обработка и получение необходимых данных
        self.adaptec_name = f"{root.attrib['deviceName']}"
        for physical_drives in root:
            drive = physical_drives.attrib['id']
            drives.append(physical_drives.attrib['id'])
            self.one_drive_report = {}
            for drives_attrib in physical_drives:
                param_id = drives_attrib.attrib['id']
                if param_id in DRIVE_PARAMETERS:
                    param_name = DRIVE_PARAMETERS[param_id]
                    if param_name == 'Media Wearout Indicator':
                        param_value = drives_attrib.attrib["normalizedWorst"]  # TODO найти правильный параметр
                    else:
                        param_value = drives_attrib.attrib["rawValue"]
                    self.one_drive_report.update({param_name: param_value})
                self.report.update({f'id={drive}': copy.deepcopy(self.one_drive_report)})
            self.drives_count = len(drives)

    def sort_by_id(self, item):
        """Return numerical room given a (name, room_number) tuple."""
        name, room = item
        _, self.sorta = room.split()
        print(self.sorta)
        return int(self.sorta)

    def run(self):
        """
        Запуск обработчика.
        :return: drives_count - количество дисков, подключенных к adaptec;
                 adaptec_name - имя adaptec;
                 report - итоговый отчет в виде словаря
        """
        # Получение и обработка данных с дисков
        self.get_adaptec_smart_data()
        self.get_adaptec_smart_report()

        # Удаление временного xml-файла
        os.remove(TMP_XML_PATH)

        return self.drives_count, self.adaptec_name, dict(sorted(self.report.items(), key=self.sort_by_id))
