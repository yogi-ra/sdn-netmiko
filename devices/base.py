from netmiko import ConnectHandler
from ntc_templates.parse import ParsingException


class Connection:
    def __init__(
        self,
        device_type=None,
        host=None,
        username=None,
        password=None,
        secret=None,
        port=None,
        **kwargs,
    ):
        """
        :param (device_type): device type that you are going to remote
        :param (host): ip or domain of device you are going to remote
        :param (username): username to connect to the device
        :param (password): password to connect to the device
        :param (secret): secret to elevate to enable mode (optional)
        :param (port): port enable of the device (optional, default: 22)
        :param (kwargs): all available paramiko params, please refer to the docs https://ktbyers.github.io/netmiko/docs/netmiko/base_connection.html
        """
        self.host = host
        self.device = {
            "device_type": device_type,
            "host": self.host,
            "username": username,
            "password": password,
            "port": (port if port is not None else 22),
            "secret": secret,
        }

        self.other_args = kwargs

    def __enter__(self):
        self.remote_conn = ConnectHandler(**self.device, **self.other_args)
        return self

    def to_enable_mode(self):
        self.remote_conn.enable()
        if self.remote_conn.check_config_mode():
            self.remote_conn.exit_config_mode()

    def to_config_mode(self):
        if self.remote_conn.check_enable_mode():
            self.remote_conn.config_mode()

    def __exit__(self, *args):
        self.remote_conn.disconnect()


class CommandProcessor:
    """Network devices raw command handler"""

    def __init__(
        self,
        connection: Connection,
        command,
        mode: str = "config",
        use_textfsm: bool = True,
        fallback_template: str = "",
    ):
        """
        :param connection: Connection object from Connection class
        :param command: raw command
        :param mode: mode to run command on (option: enable, config)
        :param use_textfsm: parse raw output (default: True)
        :param fallback_template: provide template name from ntc-templates or a full path
        """
        self.command = command
        self.connection = connection
        self.mode = mode
        self.use_textfsm = use_textfsm
        self.fallback_template = fallback_template

    def execute(self):
        self.execute_status = 0

        if self.mode == "enable":
            self.connection.to_enable_mode()

        if self.mode == "config":
            self.connection.to_config_mode()

        try:
            kwargs = {
                "use_textfsm": True,
                "raise_parsing_error": True,
            }

            if not self.use_textfsm:
                kwargs["use_textfsm"] = False

            if self.fallback_template:
                kwargs["textfsm_template"] = self.fallback_template

            self.command_output = self.connection.remote_conn.send_command(
                self.command, **kwargs
            )

            self.execute_status = 1
        except Exception:
            self.execute_status = 0
            self.command_output = ""

    def output(self) -> list:
        """
        Parsed output
        if output[0] equals 0, command failed
        if output[0] equals 1, you good to go
        if output[0] equals 2, parse failed
        """
        try:
            self.execute()
            return [
                self.execute_status,
                self.command_output,
            ]
        except ParsingException:
            return [
                2,  # Parse fails
                self.command_output,
            ]
        except Exception as e:
            return [
                self.execute_status,
                "Failed to run command: " + str(e),
            ]
