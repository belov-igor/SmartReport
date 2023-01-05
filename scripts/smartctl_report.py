import subprocess


# DISC_PARAMETERS = {
#     '0x09': 'Power-On Hours',
#     '0x05': 'Reallocated Sectors Count',
#     '0xC5': 'Current Pending Sector Count',
#     '0xC6': 'Uncorrectable Sectors Count'
# }
#

class SmartCtlReport:

    def __init__(self, username, hostname):
        self.username = username
        self.hostname = hostname
        self.report = dict()
        self.drives_count = 0
        self.smartctl_script_result = None

    def get_smartctl_data(self):
        """
        :return
        """
        open_script = subprocess.Popen(['cat /root/bin/smartctl_script.sh'], stdout=subprocess.PIPE,
                                       shell=True)  # TODO использовать скрипт из папки
        ssh_connect = subprocess.Popen([f'ssh {self.username}@{self.hostname}'], stdin=open_script.stdout,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        open_script.stdout.close()
        self.smartctl_script_result = ssh_connect.communicate()[0].decode().split('\n')

    def get_smartctl_report(self):
        """

        :return:
        """
        power_on_hours, reallocated_sector_ct, current_pending, offline_uncorrectable = '-', '-', '-', '-'
        sg_name = str()
        sg_list = list()
        for string in self.smartctl_script_result:
            if "/dev/" in string.lower():
                sg_name = string[5:]
                sg_list.append(sg_name)
                self.drives_count = len(sg_list)
            if 'reallocated' in string.lower():
                reallocated_sector_ct = int(string.split()[-1])
            if 'power_on_hours' in string.lower():
                power_on_hours = int(string.split()[9])
            if 'current_pending' in string.lower():
                current_pending = int(string.split()[-1])
            if 'offline_uncorrectable' in string.lower():
                offline_uncorrectable = int(string.split()[-1])
            self.report.update({sg_name: {'Power-On Hours': power_on_hours,
                                          'Reallocated Sectors Count': reallocated_sector_ct,
                                          'Current Pending Sector Count': current_pending,
                                          'Uncorrectable Sectors Count': offline_uncorrectable}})

    def run(self):
        #
        self.get_smartctl_data()
        self.get_smartctl_report()

        return self.drives_count, self.report
