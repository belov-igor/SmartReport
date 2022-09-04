# -*- coding: utf-8 -*-

import pandas as pd
import smtplib
import pretty_html_table
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_TO_EMAILS = '/Users/bisgarik/PycharmProjects/SmartReport/from_to_emails.txt'


class SmartReportSender:

    def __init__(self, report_result):
        self.report_result = report_result
        self.mailserver_info_path = ''
        self.message = None
        self.table = None
        self.main_table = None
        self.msg = None
        self.server = None
        self.df = None
        self.to_ = ''
        self.from_ = ''
        self.mailserver_info = None
        self.mailserver_info_list = []

    def get_mailserver_info(self, mailserver_info_path):
        self.mailserver_info_path = mailserver_info_path
        with open(self.mailserver_info_path) as self.mailserver_info:
            for line in self.mailserver_info:
                self.mailserver_info_list.append(line[:-1])
            self.from_ = self.mailserver_info_list[0]
            self.to_ = self.mailserver_info_list[1]

    def get_data_frame(self):
        self.df = pd.DataFrame.from_dict(data=self.report_result, orient='index')
        self.df.to_html()
        self.table = pretty_html_table.build_table(df=self.df, color='blue_light', index=True)

    def smtp_connect(self):
        """
        Подключение к SMTP серверу
        :return:
        """
        self.server = smtplib.SMTP('mx.prolog.ltd')  # TODO make server getting from file

    def create_message(self):
        self.msg = MIMEMultipart('alternative')
        self.msg['Subject'] = 'Adaptec report'
        self.msg['From'] = self.from_
        self.msg['To'] = self.to_
        self.main_table = MIMEText('<h3>Adaptec report</h3>', 'html')
        self.table = MIMEText(self.table, 'html')
        self.msg.attach(self.table)

    def send_message(self, message):
        self.message = message
        self.server.send_message(message=self.msg)

    def run(self):
        self.get_mailserver_info(mailserver_info_path=FROM_TO_EMAILS)
        self.get_data_frame()
        # self.smtp_connect()
        self.create_message()
        # server.send_message(msg)
        print(self.df)
        # server.quit()


if __name__ == '__main__':
    data = {'test1': {'rootvol': 'Optimal'},
            'test2': {'rootvol': 'Optimal', 'datavol': 'Optimal'},
            'test3': {'rootvol': 'Optimal', 'datavol1': 'Optimal', 'datavol2': 'Optimal', 'ssdvol': 'Optimal'}
            }

    report_message = SmartReportSender(report_result=data)
    report_message.run()