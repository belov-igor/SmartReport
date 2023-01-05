# -*- coding: utf-8 -*-
import copy
import os
import subprocess
import xml.etree.ElementTree as ETree

BASE_DIR = os.path.dirname(os.path.abspath(__package__))
TMP_XML_PATH = os.path.join(BASE_DIR, 'tmp')  # TODO подставить в проект

DISC_PARAMETERS = {
    '0x09': 'Power-On Hours',
    '0x05': 'Reallocated Sectors Count',
    '0xC5': 'Current Pending Sector Count',
    '0xC6': 'Uncorrectable Sectors Count'
}


class AdaptecSmartReport:
    """

    """
    def __init__(self, username, hostname, adaptec_num=1):
        """
        :param username: имя пользователя при подключении к удаленному хосту
        :param hostname: имя удаленного хоста
        :param adaptec_num: порядковый номер adaptec (если подключено больше 1-го) # TODO реализовать один адаптек по умолчанию
        """
        self.username = username
        self.hostname = hostname
        self.adaptec_num = adaptec_num
        self.report = dict()
        self.drives_count = 0
        self.min_string = 0
        self.max_string = 0
        self.adaptec_name = str()
        self.adaptec_smart_data = None
        self.one_drive_report = {}

    def get_adaptec_smart_data(self):
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
            ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETSMARTSTATS", f"{self.adaptec_num}"],
            stdout=subprocess.PIPE)
        self.adaptec_smart_data = connect.stdout.decode().split('\n')
        for string in self.adaptec_smart_data:
            if '<SmartStats' in string:
                self.min_string = self.adaptec_smart_data.index(string)
            if '</SmartStats>' in string:
                self.max_string = self.adaptec_smart_data.index(string) + 1
        with open(f'/tmp/smartstats_temp.xml', 'w') as smartstats_xml:
            xml = '\n'.join(self.adaptec_smart_data[self.min_string:self.max_string]) + '\n'
            smartstats_xml.write(xml)

    def get_adaptec_smart_report(self):
        """

        :return:
        """
        drives = []
        stats = ETree.parse(f'/tmp/smartstats_temp.xml')  # TODO сохранять xml в tmp проекта
        # Найти корень
        root = stats.getroot()
        self.adaptec_name = f"{root.attrib['deviceName']}"
        for physical_drives in root:
            drive = physical_drives.attrib['id']
            drives.append(physical_drives.attrib['id'])
            self.one_drive_report = {}
            for drives_attrib in physical_drives:
                param_id = drives_attrib.attrib['id']
                if param_id in DISC_PARAMETERS:
                    param_name = DISC_PARAMETERS[param_id]
                    param_value = drives_attrib.attrib["rawValue"]
                    self.one_drive_report.update({param_name: param_value})
                self.report.update({f'id={drive}': copy.deepcopy(self.one_drive_report)})
            self.drives_count = len(drives)

    def run(self):

        #
        self.get_adaptec_smart_data()
        self.get_adaptec_smart_report()
        #
        os.remove(f'/tmp/smartstats_temp.xml')

        return self.drives_count, self.adaptec_name, self.report
