# -*- coding: utf-8 -*-

import smtplib


def send_email(host, subject, from_addr, to_addr, body):
    """
    :param host:
    :param subject:
    :param from_addr:
    :param to_addr:
    :param body:
    """
    server = smtplib.SMTP(host=host, port=25)

    mail_body = "\r\n".join((
        "From: %s" % from_addr,
        "To: %s" % to_addr,
        "Subject: %s" % subject,
        "",
        body
    ))

    # server.sendmail(from_addr, to_addr, mail_body)
    # server.quit()
