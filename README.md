# SmartReport
SmartReport - инструмент для мониторинга состояния дисков на удаленных хостах. Он позволяет проверять и анализировать данные SMART (Self-Monitoring, Analysis and Reporting Technology) для обнаружения проблем и предупреждения о возможных отказах дисков.

## Установка
Клонируйте репозиторий SmartReport на ваше локальное устройство:

'''bash
git clone https://github.com/belov-igor/SmartReport.git
Установите необходимые зависимости:

Copy code
pip install -r requirements.txt
Настройка
Перед использованием проекта вам необходимо выполнить несколько шагов настройки.

Откройте файл config/email_server.py и настройте SMTP-сервер, отправителя и получателя для отправки отчетов по электронной почте:

python
Copy code
SMTP_SERVER = 'your_smtp_server'
FROM = 'sender@example.com'
TO = 'recipient@example.com'
Откройте файл config/hosts.py и настройте списки хостов, которые будут проверяться для мониторинга дисков. Список хостов, использующих smartctl, определен в словаре SMARTCTL_HOSTS, где ключ - имя хоста, а значение - имя пользователя для подключения к хосту. Список хостов, использующих Adaptec, определен в словаре ADAPTEC_HOSTS в том же формате.

Пример конфигурации для хостов, использующих smartctl:

python
Copy code
SMARTCTL_HOSTS = {
    'host1': 'user1',
    'host2': 'user2',
    'host3': 'user3',
}
Пример конфигурации для хостов, использующих Adaptec:

python
Copy code
ADAPTEC_HOSTS = {
    'host4': 'user4',
    'host5': 'user5',
    'host6': 'user6',
}
Использование
Для запуска проекта SmartReport выполните следующие шаги:

Перейдите в корневую директорию проекта:

bash
Copy code
cd SmartReport
Запустите файл run.py:

arduino
Copy code
python run.py
Проект будет сканировать указанные хосты и собирать данные о состоянии дисков. Результаты будут сгенерированы в виде HTML-таблиц и отправлены на указанный адрес электронной почты.

Проверьте свою почту, чтобы просмотреть полученные отчеты SMART.
