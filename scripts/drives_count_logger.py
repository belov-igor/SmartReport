# -*- coding: utf-8 -*-
from datetime import date


def drive_count_logger(host, drives_count, old_path, new_path):
    old_date = ''
    disc_count_old = ''
    with open(old_path, 'r') as drive_count_log_old:
        for line in drive_count_log_old:
            if host in line.split():
                old_date = line.split()[1]
                disc_count_old = line.split()[2]
    with open(new_path, 'a') as drive_count_log_new:
        new_date = date.today().strftime("%d.%m.%Y")
        drive_count_log_new.write(f'{host} {new_date} {drives_count}\n')
    return f'Всего дисков на сегодня ({new_date}) - <b>{drives_count}</b>. ' \
           f'Дисков при прошлой проверке ({old_date}) - <b>{disc_count_old}</b>.'