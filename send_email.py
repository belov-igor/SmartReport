import pandas as pd
import smtplib
import pretty_html_table
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_TO_EMAILS = '/Users/bisgarik/PycharmProjects/SmartReport/from_to_emails.txt'


class SmartReportSender:

    def __init__(self, report_result):
        self.server = None
        self.df = None
        self.to_ = ''
        self.from_ = ''
        self.mailserver_info = []
        self.report_result = report_result
        self.mail_info_1 = []

    def get_mailserver_info(self, mailserver_info):
        self.mailserver_info = mailserver_info
        with open(FROM_TO_EMAILS) as self.mailserver_info:
            for line in self.mailserver_info:
                self.mailserver_info.append(line[:-1])
            self.from_ = self.mailserver_info[0]
            self.to_ = self.mailserver_info[1]

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
        pass

    def run(self):
        # server.send_message(msg)
        # print(df)
        # server.quit()
        pass






    data = {'test1': {'rootvol': 'Optimal'},
            'test2': {'rootvol': 'Optimal', 'datavol': 'Optimal'},
            'test3': {'rootvol': 'Optimal', 'datavol1': 'Optimal', 'datavol2': 'Optimal', 'ssdvol': 'Optimal'}
            }

    # df = pd.DataFrame.from_dict(data=data, orient='index')
    # df.to_html()
    # table = pretty_html_table.build_table(df=df, color='blue_light', index=True)

    # подключаемся к SMTP серверу
    # server = smtplib.SMTP('mx.prolog.ltd')  # TODO make server getting from file

    # создаём письмо
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Adaptec report'
    msg['From'] = from_
    msg['To'] = to_

    #
    main_table = MIMEText('<h3>Adaptec report</h3>', 'html')
    table = MIMEText(table, 'html')

    msg.attach(table)

    # server.send_message(msg)
    print(df)
    # server.quit()
