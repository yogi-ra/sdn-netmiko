from datetime import datetime
from re import search
import pytz

from devices.base import (
    Connection,
    CommandProcessor
)

class CiscoBasic(Connection):
    """Basic Cisco IOS and XE device management"""
    def version(self) -> list:
        """Execute show version command."""
        command_str = "show version"
        command = CommandProcessor(self, command_str, "enable")
        command_output = command.output()

        if command_output[0] == 1:
            return command_output[1]
        else:
            return f"Command execution fails {command_output[1]}"

    @property
    def clock(self) -> datetime:
        """Returns the time and date on the device."""
        command_str = "show clock"
        command = CommandProcessor(self, command_str, "enable")
        command_output = command.output()

        if command_output[0] == 1:
            clock_raw = command_output[1]
            clock_list = list(clock_raw[0].values())
            if len(clock_list[0].split(".")[1]) < 6:
                clock_list[0] += "000"
            clock_str = " ".join(clock_list)
        else:
            return f"Command execution fails {command_output[1]}"

        clock = datetime.strptime(clock_str, "%H:%M:%S.%f %Z %a %b %d %Y")

        clock_utc = pytz.utc.localize(clock)
        return clock_utc.strftime("%H:%M:%S %Z %a %b %d %Y")

    @clock.setter
    def clock(self, datetime_obj: datetime) -> datetime:
        """
        Sets the clock of the device using Netmiko.
        :param datetime_obj: an instance of the datetime.datetime class
        """
        command_str = "show clock"
        command = CommandProcessor(self, command_str, "enable")
        command_output = command.output()

        if isinstance(datetime_obj, datetime):
            equipment_date_raw_values = command_output[0].values()
            if len(equipment_date_raw_values[0]) < 6:
                equipment_date_raw_values[0] += '000'
            
            equipment_date = datetime.strptime(
                equipment_date_raw_values,
                "%H:%M:%S.%f %Z %a %b %d %Y"
            )

            timedelta = abs((equipment_date - datetime_obj).total_seconds())

            if timedelta > 30:
                date = datetime_obj.strftime("%H:%M:%S %d %b %Y")
                command_str = f"clock set {date}"
                command = CommandProcessor(self, command_str, "enable")
                command.execute()
        else:
            raise ValueError("Must assign a datetime object.")

    @property
    def hostname(self) -> str:
        """Returns the hostname of the device."""
        name = self.remote_conn.find_prompt().replace("(config)", "")
        name = name.replace("#", "")
        name = name.replace(">", "")
        return name

    @hostname.setter
    def hostname(self, name: str):
        """
        Sets the hostname of the device.
        :param name: must contain at least one alphabet or '-' or '_' character
        """
        if search("[a-zA-z_-]", name):
            command_str = f"hostname {name}"
            command = CommandProcessor(self, command_str, mode="config")
            command.execute()
        else:
            raise ValueError("Hostname should contain at least one alphabet or '-' or '_' character")

    def get_users(self) -> list:
        """Returns a list of configured users."""
        command_str = "show running-config | include username"
        command = CommandProcessor(self, command_str, mode="enable", use_textfsm=False)
        command_output = command.output()
        if command_output[0] == 1:
            users_str = command_output[1].split('\n')
        else:
            return f"Command execution fails {command_output[1]}"

        user_list = []
        for line in users_str:
            user_list.append(line.split()[1])
        return user_list

    def get_active_users(self) -> list:
        """Returns a list of active users."""
        command_str = "show users"
        command = CommandProcessor(self, command_str, mode="enable")
        command_output = command.output()
        if command_output[0] == 1:
            return command_output[1]
        else:
            return f"Command execution fails {command_output[1]}"

    def add_user(self, username: str, password: str, privilege: int):
        """
        Adds user

        :param username: username
        """
        if privilege >= 1 and privilege <= 15:
            pass
        else:
            raise ValueError("Wrong privilege level provided")

        command_str = f"username {username} privilege {privilege} password {password}"
        command = CommandProcessor(self, command_str, mode="config")
        command.execute()

    def delete_user(self, username: str):
        command_str = f"no username {username}"
        command = CommandProcessor(self, command_str, mode="config")
        command.execute()

    def get_current_user_privilege(self) -> int:
        command_str = "show privilege"
        command = CommandProcessor(self, command_str, mode="enable", use_textfsm=False)
        return command.output()[1].split()[-1]

    @property
    def domain(self) -> str:
        """Returns the domain name configured on the device."""
        command_str = "show running-config | include domain"
        command = CommandProcessor(self, command_str, mode="enable", use_textfsm=False)
        return command.output()[1].split()[-1]

    @domain.setter
    def domain(self, domain_name: str):
        """
        Sets the domain-name of the device.
        :param domain_name: domain name of the device
        """
        self.to_config_mode()
        self.remote_conn.send_command(f"ip domain-name {domain_name}")
    
    def show_interfaces(self) -> list:
        """Show device interfaces"""
        command_str = "show interfaces"
        command = CommandProcessor(self, command_str, mode="enable")
        return command.output()[1]

    def save_configuration(self):
        """Save configurations to startup-config"""
        self.to_enable_mode()
        self.remote_conn.send_command("write memory")

class CiscoSwitch(Connection):
    """Cisco IOS and XE Switch Management"""
    def show_vlans(self) -> list:
        command_str = "show vlan"
        command = CommandProcessor(self, command_str, "enable")
        command_output = command.output()

        if command_output[0] == 1:
            return command_output[1]
        else:
            return f"Command execution fails {command_output[1]}"
    
    def show_vlan(self, vlan_id: int):
        command_str = "show vlan brief"
        command = CommandProcessor(self, command_str, "enable")
        command_output = command.output()

        if command_output[0] == 1:
            for i, vlan in enumerate(command_output[1]):
                if int(vlan["vlan_id"]) == vlan_id:
                    return command_output[1][i]
            return "There's no such vlan"
        else:
            return f"Command execution fails {command_output[1]}"
        
    def set_vlan(self, vlan_id: int, vlan_name: str):
        command_str = f"vlan {vlan_id}\nname {vlan_name}"
        command = CommandProcessor(self, command_str, "config")
        command.execute()