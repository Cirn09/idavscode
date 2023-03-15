import sys
import asyncio
import json
import threading
import debugpy
import tornado.httpserver, tornado.web, tornado.websocket

from .config import Config
from .utils import PythonFile

class MessageType(object):
    StartDebugServer = 'startDebugServer'
    StopDebugServer = 'stopDebugServer'
    StopServer = 'stopServer'
    ExecuteScript = 'executeScript'

    ServerReady = 'serverReady'
    DebugServerReady = 'debugServerReady'
    DebugFinished = 'debugFinished'
    Error = 'error'

dbgsrv_running = False

class DebugServerCannotStopError(Exception):
    pass


class _Server(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(_Server, self).__init__(*args, **kwargs)

    def on_message(self, message: str):
        global dbgsrv_running
        msg: dict = json.loads(message)
        try:
            
            match msg['type']:
                case MessageType.StartDebugServer:
                    if not dbgsrv_running:
                        host = msg['host']
                        port = msg['port']
                        logfile = msg['logfile']
                        python_path = msg['pythonPath']

                        if logfile:
                            debugpy.log_to(logfile)
                            print(f'[VSC] Debug log will be saved to {logfile}')
                        if python_path:
                            debugpy.configure({ "python": python_path })
                            print(f'[VSC] Python path set to {python_path}')

                        debugpy.listen((host, port))
                        print(f'[VSC] Debug server started on {host}:{port}')
                        dbgsrv_running = True
                    self.write_message({'type': MessageType.DebugServerReady})
                    
                case MessageType.StopDebugServer:
                    # https://github.com/microsoft/debugpy/issues/870
                    self.write_message({'type': MessageType.Error, 'info': 'Not implemented'})
                    raise NotImplementedError
                case MessageType.StopServer:
                    self.write_message({'type': MessageType.ServerReady})
                    print('[VSC] Server stopped')
                    self.close()
                case MessageType.ExecuteScript:
                    if not dbgsrv_running:
                        self.write_message({'type': MessageType.Error, 'info': 'debug server is not running'})
                        return

                    path = msg['path']
                    cwd = msg['cwd']
                    argv = msg.get('argv', [])
                    env = msg.get('env', {})
                    encoding = msg.get('encoding', None)
                    print(f'[VSC] Executing script {path}')

                    pf = PythonFile(path, cwd, argv, env, encoding)

                    self.write_message({'type': MessageType.ServerReady})

                    debugpy.wait_for_client()
                    pf.exec()

                    self.write_message({'type': MessageType.DebugFinished})


                case _:
                    print(f'[VSC] Unknown message type {msg["type"]}')
                    self.write_message({'type': MessageType.Error, 'info': 'Unknown message type'})
        except Exception as e:
            info = f'{e.__class__.__name__}: {e}'
            self.write_message({'type': MessageType.Error, 'info': info})
            print(f'[!!!] {info}')

    def on_close(self) -> None:
        print('[VSC] Connect closed')


class Server(object):
    def __init__(self, config:Config):
        self.config = config
        self.app = tornado.web.Application([(r'/', _Server)])
        self.server = tornado.httpserver.HTTPServer(self.app)
        self.thread = threading.Thread(target=self._start)
        self.thread.daemon = True
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
                self.thread.daemon = True
            self.thread.start()
        else:
            print('[VSC] server is already running')
    
    def _start(self):
        # if sys.version_info >= (3, 4):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.server.listen(address=self.config.host, port=self.config.port)
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()

    def stop(self):
        '''stop server'''
        global dbgsrv_running
        if not self.running:
            return
        # self.ioloop.stop()
        # self.ioloop = None
        self.ioloop.add_callback(self.ioloop.stop)
        # asyncio.new_event_loop().run_until_complete(self.server.close_all_connections())
        self.server.stop()
        self.thread.join()
        
        self.thread = threading.Thread(target=self._start)
        self.thread.daemon = True

        if dbgsrv_running:
            raise DebugServerCannotStopError('Debug server cannot be stopped currently.\ncheck here: https://github.com/microsoft/debugpy/issues/870')
