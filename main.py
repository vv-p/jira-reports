# -*- coding: utf-8 -*-

import smtplib
import arrow

from email.mime.text import MIMEText


def send_on_email(report, subject, mail_from, mail_to, smtp_auth):
    smtp_login, smtp_password = smtp_auth

    msg = MIMEText(report.encode('utf-8'), 'html', 'utf-8')
    msg["Subject"] = subject
    msg["From"] = mail_from
    to = ', '.join(mail_to.split())
    msg["To"] = to

    s = smtplib.SMTP_SSL('smtp.mail.ru', 465)
    # s.set_debuglevel(2)  # ToDo: parametrize it
    s.login(smtp_login, smtp_password)
    s.sendmail(smtp_login, mail_to, msg.as_string())  # sender address must match authenticated user


def get_day_offset():
    now = arrow.now()
    offsets = (3, 1, 1, 1, 1, 1, 2)
    return offsets[now.weekday()]


def get_jira_list(l):
    """
    Format any lists to jira string  
    :param l: list to format ["aaa", "bbb", "ccc"]
    :return: string looks like '"aaa", "bbb", "ccc"'
    """
    return ', '.join('"%s"' % x for x in l)
