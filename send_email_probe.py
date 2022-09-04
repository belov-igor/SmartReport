import pandas as pd
import smtplib
import pretty_html_table
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

mail_info_1 = []

with open('/Users/bisgarik/PycharmProjects/SmartReport/from_to_emails.txt') as mail_info:
    for line in mail_info:
        mail_info_1.append(line[:-1])
    from_ = mail_info_1[0]
    to_ = mail_info_1[1]

    data = {'test1': {'rootvol': 'Optimal'},
            'test2': {'rootvol': 'Optimal', 'datavol': 'Optimal'},
            'test3': {'rootvol': 'Optimal', 'datavol1': 'Optimal', 'datavol2': 'Optimal', 'ssdvol': 'Optimal'}
            }

    df = pd.DataFrame.from_dict(data=data, orient='index')
    df.to_html()
    table = pretty_html_table.build_table(df=df, color='blue_light', index=True)

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
