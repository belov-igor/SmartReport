# -*- coding: utf-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_server import SMTP_SERVER, FROM, TO


class ReportSender:

    def __init__(self, subject, body):
        self.body = body
        self.subject = subject
        self.message = None
        self.body = None
        self.main_table = None
        self.msg = None
        self.server = None
        self.df = None

    # def get_data_frame(self):
    #     self.df = pd.DataFrame.from_dict(data=self.report_result, orient='index')
    #     self.df.to_html()
    #     self.table = pretty_html_table.build_table(df=self.df, color='blue_light', index=True)

    def smtp_connect(self):
        """
        Подключение к SMTP серверу
        :return:
        """
        self.server = smtplib.SMTP(SMTP_SERVER)

    def create_message(self):
        self.msg = MIMEMultipart('alternative')
        self.msg['Subject'] = self.subject
        self.msg['From'] = FROM
        self.msg['To'] = TO
        self.body = MIMEText(self.body, 'html')
        self.msg.attach(self.body)

    def send_message(self, message):
        self.message = message
        self.server.send_message(msg=self.msg)

    def run(self):
        # self.get_data_frame()
        self.smtp_connect()
        self.create_message()
        self.send_message(self.msg)
        self.server.quit()


if __name__ == '__main__':
    data = {'test1': {'rootvol': 'Optimal'},
            'test2': {'rootvol': 'Optimal', 'datavol': 'Optimal'},
            'test3': {'rootvol': 'Optimal', 'datavol1': 'Optimal', 'datavol2': 'Optimal', 'ssdvol': 'Optimal'}
            }

    report_message = ReportSender(subject='Adaptec report',
                                  body=data)
    report_message.run()
