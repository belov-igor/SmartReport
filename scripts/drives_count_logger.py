from datetime import date


def drive_count_logger(host, drives_count, old_path, new_path, adaptec_num=0):
    """
    Функция для получения данных о количестве дисков хоста из файла-лога (при предыдущем исполнении)
    и запись существующего количества в новый лог.

    :param host: имя удаленного хоста;
    :param drives_count: количество дисков на данный момент;
    :param old_path: путь к логу-результату предыдущей обработки;
    :param new_path: путь к логу-результату текущей обработки;
    :param adaptec_num: по умолчанию (при отсутствии adaptec) = 0
                        при использовании adaptec - порядковый номер.
    :return: текстовое сообщение с html-тегами о количестве дисков хоста и сравнении с предыдущей обработкой
    """
    old_date = str()
    drives_count_old = str()
    color = 'black'

    # Открытие файла лога с количеством дисков при предыдущей обработке и получение данных
    with open(old_path, 'r') as drive_count_log_old:
        for line in drive_count_log_old:
            if host in line.split():
                if adaptec_num == int(line.split()[1]):
                    old_date = line.split()[2]
                    drives_count_old = int(line.split()[3])

    # Запись нового лога с количеством дисков при текущей обработке
    with open(new_path, 'a') as drive_count_log_new:
        new_date = date.today().strftime("%d.%m.%Y")
        drive_count_log_new.write(f'{host} {adaptec_num} {new_date} {drives_count}\n')

        # Цвет шрифта количества дисков будет красным, если количество дисков не совпадает
        if drives_count != drives_count_old:
            color = 'red'

    return f'Всего дисков на сегодня ({new_date}) - ' \
           f'<span style="color: {color}; font-weight: bold">{drives_count}</span>. '\
           f'Дисков при прошлой проверке ({old_date}) - ' \
           f'<span style="font-weight: bold">{drives_count_old}</span>.'
