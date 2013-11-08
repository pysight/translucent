# -*- coding: utf-8 -*-

import sys
if 'threading' in sys.modules:
    del sys.modules['threading']
from gevent import monkey
monkey.patch_all()
import os
from flask import Flask, Response, request
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from werkzeug.serving import run_with_reloader

from .debugger import SocketIODebugger


class App(object):

    def __init__(self):
        pass

    def on_init(self):
        pass

    def on_start(self):
        pass


class SocketIONamespace(BaseNamespace):

    def on_hello(self, data):
        print 'hello received:', data
        self.emit('hello')

    def recv_connect(self):
        print 'recv_connect()'

    def recv_disconnect(self):
        print 'disconnect()'
        self.disconnect(silent=True)


class Server(object):

    def __init__(self, app, ui, host='127.0.0.1', port=5000, debug=True):
        if isinstance(app, App):
            self.app = app
            app.on_init()
        else:
            raise Exception('app must be an instance of App')
        self.host, self.port = host, port
        package_folder = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(package_folder, '..', 'templates')
        static_folder = os.path.join(package_folder, '..', 'static')
        self.flask_app = Flask(__name__,
            template_folder=template_folder,
            static_folder=static_folder)
        self.debug = self.flask_app.debug = debug
        self.flask_app.route('/')(self.index)
        self.flask_app.route('/socket.io/<path:path>')(self.socketio)
        self.template = ui.render_layout()

    def run(self):
        try:
            print 'Listening at %s port %d...' % (self.host, self.port)
            if self.debug:
                self.flask_app = SocketIODebugger(self.flask_app,
                    evalex=True, namespace=SocketIONamespace)
            server = SocketIOServer((self.host, self.port), self.flask_app,
                resource='socket.io', policy_server=False)
            if self.debug:
                run_with_reloader(lambda: server.serve_forever())
            else:
                server.serve_forever()
        except KeyboardInterrupt:
            print '\rShutting down...'

    def socketio(self, path):
        try:
            socketio_manage(request.environ,
                {'/api': SocketIONamespace}, request)
        except:
            self.flask_app.logger.error('socket.io exception', exc_info=True)
        return Response()

    def index(self):
        return self.template
