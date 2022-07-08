import sys
import asyncio
import json
import threading
from enum import Enum
import debugpy
import tornado.httpserver, tornado.web, tornado.websocket

from .config import Config
from .utils import execfile

class MessageType(Enum):
    StartDebugServer = 'start_debug_server'
    StopDebugServer = 'stop_debug_server'
    StopServer = 'stop_server'
    ExecuteScript = 'execute_script'

    ServerReady = 'server_ready'
    Error = 'error'


class DebugServerCannotStopError(Exception):
    pass


class _Server(tornado.websocket.WebSocketHandler):
    dbgsrv_running = False

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
        self.dbgsrv_running = False

    def on_message(self, message):
        msg = json.loads(message.decode("utf8"))
        
        match msg['type']:
            case MessageType.StartDebugServer:
                if not self.dbgsrv_running:
                    host = msg['host']
                    port = msg['port']
                    logfile = msg['logfile']
                    python_path = msg['python_path']

                    if logfile:
                        debugpy.log_to(logfile)
                        print(f'[VSC] Debug log will be saved to {logfile}')
                    if python_path:
                        debugpy.configure({ "python": python_path })
                        print(f'[VSC] Python path set to {python_path}')

                    debugpy.start_server((host, port))
                    print(f'[VSC] Debug server started on {host}:{port}')
                    self.dbgsrv_running = True
                self.write_message({'type': MessageType.ServerReady})
                
            case MessageType.StopDebugServer:
                # https://github.com/microsoft/debugpy/issues/870
                self.write_message({'type': MessageType.Error, 'info': 'Not implemented'})
                raise NotImplementedError
            case MessageType.StopServer:
                self.write_message({'type': MessageType.ServerReady})
                print('[VSC] Server stopped')
                self.close()
            case MessageType.ExecuteScript:
                if not self.dbgsrv_running:
                    self.write_message({'type': MessageType.Error, 'info': 'debug server is not running'})
                    return

                path = msg['path']
                cwd = msg['cwd']
                argv = msg['argv']
                env = msg['env']
                encoding = msg['encoding']
                print(f'[VSC] Executing script {path}')
                debugpy.wait_for_client()
                execfile(path, cwd, argv, env, encoding)

    def on_close(self) -> None:
        print('[VSC] Connect closed')


class Server(object):
    def __init__(self, config:Config):
        self.config = config
        self.app = tornado.web.Application([(r'/', _Server)])
        self.server = tornado.httpserver.HTTPServer(self.app)
        self.thread = threading.Thread(target=self._start)
        self.thread.daemon = False
        self.ioloop = None
        
    @property
    def running(self):
        return self.thread.is_alive()

    def start(self):
        '''start server'''
        if not self.running:
            if self.thread.ident is not None:
                # threads can only be started once
                self.thread = threading.Thread(target=self._start)
                self.thread.daemon = False
            self.thread.start()
        else:
            print('server is already running')
    
    def _start(self):
        # if sys.version_info >= (3, 4):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.server.listen(address=self.config.host, port=self.config.port)
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()

    def stop(self):
        '''stop server'''
        if not self.running:
            return
        # self.ioloop.stop()
        # self.ioloop = None
        self.ioloop.add_callback(self.ioloop.stop)
        # asyncio.new_event_loop().run_until_complete(self.server.close_all_connections())
        self.server.stop()
        self.thread.join()
        
        self.thread = threading.Thread(target=self._start)
        self.thread.daemon = False

        if self.app.wildcard_router.rules[0].target.dbgsrv_running:
            raise DebugServerCannotStopError('Debug server cannot be stopped currently.\ncheck here: https://github.com/microsoft/debugpy/issues/870')
