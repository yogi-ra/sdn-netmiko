from datetime import datetime
from re import search
import pytz

from devices.base import Connection, CommandProcessor


class CiscoBasic(Connection):
    """Cisco Basic Commands"""

    def version(self) -> list:
        """Execute show version command."""
        command = CommandProcessor(self, "show version")
        return command.output()

    @property
    def clock(self) -> str:
        """Returns the time and date on the device."""
        self.to_enable_mode()
        command = CommandProcessor(self, "show clock")
        command_output = command.output()

        if command_output[0]:
            clock_str = command.output()[1].replace("*", "")
        else:
            print("Command fails")
            return ""

        self.to_config_mode()
        clock = datetime.strptime(clock_str, "%H:%M:%S.%f %Z %a %b %d %Y")
        clock_utc = pytz.utc.localize(clock)
        return clock_utc.strftime("%H:%M:%S %Z %a %b %d %Y")

    @clock.setter
    def clock(self, datetime_obj):
        """
        Sets the clock of the device using Netmiko.
        :param (datetime_obj): an instance of the datetime.datetime class
        """
        if isinstance(datetime_obj, datetime):
            equipment_date_raw = (
                str(self.remote_conn.send_command("show clock"))
                .replace("*", "")
                .strip()
            )
            equipment_date = datetime.strptime(
                equipment_date_raw, "%H:%M:%S.%f %Z %a %b %d %Y"
            )

            timedelta = abs((equipment_date - datetime_obj).total_seconds())

            if timedelta > 30:
                date = datetime_obj.strftime("%H:%M:%S %d %b %Y")
                self.remote_conn.enable()
                return self.remote_conn.send_command(f"clock set {date}")
            else:
                return f"{self.device['host']} - {equipment_date_raw} - Clock OK"
        else:
            raise ValueError("Must assign a datetime object.")

    @property
    def hostname(self) -> str:
        """Returns the hostname of the device."""
        name = self.remote_conn.find_prompt().replace("(config)#", "")
        name = name.replace("#", "")
        name = name.replace(">", "")
        return name

    @hostname.setter
    def hostname(self, name):
        """
        Sets the hostname of the device.
        :param name: (str) must contain at least one alphabet or '-' or '_' character
        """
        if search("[a-zA-z_-]", name):
            self.remote_conn.send_command(f"hostname {name}")
        else:
            raise ValueError(
                "Hostname should contain at least one alphabet or '-' or '_' character"
            )

    def get_users(self):
        """Returns a list of configured users."""
        self.to_enable_mode()

        users_str = str(
            self.remote_conn.send_command("show running-config | section username")
        ).split("\n")

        user_list = []
        for line in users_str:
            user_list.append(line.split()[1])
        return user_list

    def add_user(self, username, password, privilege=15):
        self.to_config_mode()
        self.remote_conn.send_command(
            f"username {username} privilege {privilege} password {password}"
        )

    def delete_user(self, user):
        self.to_config_mode()
        self.remote_conn.send_command(f"no username {user}")

    @property
    def domain(self):
        """Returns the domain name configured on the device."""
        self.to_enable_mode()
        domain_name = str(
            self.remote_conn.send_command("show running-config | include domain")
        ).split()[-1]
        return domain_name

    @domain.setter
    def domain(self, domain_name):
        """
        Sets the domain-name of the device.
        :param domain_name: (str) domain name of the device
        """
        self.to_config_mode()
        self.remote_conn.send_command(f"ip domain-name {domain_name}")

    def get_current_user_privilege(self):
        """Get current user privilege level"""
        self.to_enable_mode()
        privilege = int(
            str(self.remote_conn.send_command("show privilege")).split()[-1]
        )
        return privilege

    def save_configuration(self):
        """Saves configurations to startup-config"""
        self.to_enable_mode()
        self.remote_conn.send_command("write memory")


class CiscoSwitch(Connection):
    pass
