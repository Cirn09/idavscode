import os
import ida_kernwin, idaapi

from dbg_server import Config, Server, DebugServerCannotStopError

CONFIG_FILE = os.path.join(idaapi.get_user_idadir(), 'config.cfg')


# =====================================================================================
# Core
# =====================================================================================
class Plugin(idaapi.plugin_t):

    def __init__(self) -> None:
        self.comment = "IDAPython VSCode Debugger"
        self.flags = idaapi.PLUGIN_HIDE
        self.wanted_name = "IDAVSC"
        if not os.path.exists(CONFIG_FILE):
            self.config = Config()
        else:
            self.config = Config.from_file(CONFIG_FILE)
        self.server = Server(self.config)

    @property
    def running(self):
        return self.server.running

    def init(self):
        """
        This is called by IDA when it is loading the plugin.
        """
        StartMenuHandle.register(self)
        StopMenuHandle.register(self)
        OptionMenuHandle.register(self)

    def run(self, arg):
        """
        This is called by IDA when this file is loaded as a script.
        """
        pass

    def term(self):
        """
        This is called by IDA when it is unloading the plugin.
        """
        self.config.save(CONFIG_FILE)

    def start(self):
        self.server.start()
        print('[IDAVSC] Server started')

    def stop(self):
        try:
            self.server.stop()
            print('[IDAVSC] Server stopped')
        except DebugServerCannotStopError:
            dialog = ErrorDialog(
                'Control server stoped, but debug server is still running and cannot be stopped currently.\nCheck here for more: https://github.com/microsoft/debugpy/issues/870'
            )
            dialog.Execute()
            dialog.Free()

    def option(self):
        dialog = OptionDialog(self.config.host, self.config.port)
        if dialog.Execute() == 1:
            self.config.host = dialog.host
            self.config.port = dialog.port
            self.config.save(CONFIG_FILE)
        dialog.Free()


# =====================================================================================
# UI
# =====================================================================================
class MenuHandle(ida_kernwin.action_handler_t):
    NAME = ''
    TEXT = ''
    TOOLTIP = ''
    HOTKEY = None
    PATH = ''

    def __init__(self, plugin: Plugin) -> None:
        super(MenuHandle, self).__init__()
        self.plugin = plugin

    @classmethod
    def register(self, plugin: Plugin) -> None:
        desc = ida_kernwin.action_desc_t(self.NAME, self.TEXT, self(plugin),
                                         self.HOTKEY, self.TOOLTIP)
        if not ida_kernwin.register_action(desc):
            print(f'Failed to register action: {self.NAME}')
        ida_kernwin.attach_action_to_menu(self.PATH, self.NAME,
                                          ida_kernwin.SETMENU_APP)


class StartMenuHandle(MenuHandle):

    NAME = 'idavsc:start'
    TEXT = "Start"
    TOOLTIP = "Start debug server"
    PATH = 'Edit/IDAVSC/Start'

    def activate(self, ctx):
        self.plugin.start()

    def update(self, ctx):
        if self.plugin.running:
            return ida_kernwin.AST_DISABLE
        else:
            return ida_kernwin.AST_ENABLE


class StopMenuHandle(MenuHandle):
    NAME = 'idavsc:stop'
    TEXT = "Stop"
    TOOLTIP = "Stop debug server"
    PATH = 'Edit/IDAVSC/Stop'

    def activate(self, ctx):
        self.plugin.stop()

    def update(self, ctx):
        if self.plugin.running:
            return ida_kernwin.AST_ENABLE
        else:
            return ida_kernwin.AST_DISABLE


class OptionMenuHandle(MenuHandle):
    NAME = 'patching:option'
    TEXT = "Option..."
    TOOLTIP = "Option"
    PATH = 'Edit/IDAVSC/Option...'

    def activate(self, ctx):
        self.plugin.option()

    def update(self, ctx):
        return ida_kernwin.AST_ENABLE_ALWAYS


class OptionDialog(ida_kernwin.Form):

    def __init__(self, hostname, control_port):
        super(OptionDialog, self).__init__(
            r"""STARTITEM 0
BUTTON YES* OK
IDACODE :: OPTION

<Hostname       :{c_hostname}>
<Port           :{c_port}>
            """, {
                'c_hostname': self.StringInput(value=hostname),
                'c_port': self.NumericInput(value=control_port, tp=self.FT_DEC),
            })

        self.Compile()

    @property
    def hostname(self):
        return self.c_hostname.value

    @property
    def port(self):
        return self.c_port.value


class ErrorDialog(ida_kernwin.Form):

    def __init__(self, text):
        super(ErrorDialog, self).__init__(
            r"""STARTITEM 1
BUTTON YES* OK
IDACODE :: Error

<{text}>
            """, {
                'text': self.StringInput(value=text),
            })

        self.Compile()


def PLUGIN_ENTRY():
    return Plugin()
