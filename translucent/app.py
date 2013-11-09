# -*- coding: utf-8 -*-

import sys
if 'threading' in sys.modules:
    del sys.modules['threading']
from gevent import monkey
monkey.patch_all()
import os
from blinker import Signal
from flask import Flask, Response, request
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from werkzeug.serving import run_with_reloader

from .debugger import SocketIODebugger
from .reactive import *


class App(object):

    def __init__(self, namespace):
        self.namespace = namespace
        self.context = ReactiveContext()

    def on_init(self):
        pass

    @classmethod
    def on_start(cls):
        pass

    def on_connect(self):
        print 'App.on_connect'

    def on_inputs_init(self, env):
        print 'app:', env

    def on_input_update(self, key, value):
        print 'input_update:', key, value

    def set_input(self, key, value):
        self.send_value(key, value, readonly=False)

    def set_value(self, key, value, shared=False):
        if key not in self.context:
            self.context.value(key)
        self.context[key] = value
        if shared:
            self.send_value(key, value, readonly=True)

    def new_expression(self, key, fn, shared=False):
        raise NotImplemented

    def send_value(self, key, value, readonly=False):
        self.namespace.send_value(key, value, readonly)


class SocketIONamespace(BaseNamespace):

    def __init__(self, *args, **kwargs):
        super(SocketIONamespace, self).__init__(*args, **kwargs)
        self.app = self.app_class(self)
        self.app.on_init()

    def send_value(self, key, value, readonly=False):
        self.emit('value_update', {'key': key, 'value': value, 'readonly': readonly})

    def on_input_update(self, data):
        self.app.on_input_update(data['key'], data['value'])

    def on_inputs_init(self, env):
        self.app.on_inputs_init(env)

    def recv_connect(self):
        self.app.on_connect()

    def recv_disconnect(self):
        self.disconnect(silent=True)

    @classmethod
    def set_app_class(cls, app_class):
        cls.app_class = app_class


class Server(object):

    def __init__(self, app_class, ui, host='127.0.0.1', port=5000, debug=True):
        if not issubclass(app_class, App):
            raise Exception('app_class must be a subclass of App')
        self.app_class = app_class
        print 'Initializing the app...'
        self.app_class.on_start()
        self.host, self.port = host, port
        package_folder = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(package_folder, '..', 'templates')
        static_folder = os.path.join(package_folder, '..', 'static')
        self.flask_app = Flask(__name__,
            template_folder=template_folder,
            static_folder=static_folder)
        self.debug = debug
        self.flask_app.debug = debug
        self.flask_app.route('/')(self.index)
        self.flask_app.route('/socket.io/<path:path>')(self.socketio)
        self.template = ui.render_layout()

    def run(self):
        try:
            print 'Listening at %s port %d...' % (self.host, self.port)
            SocketIONamespace.set_app_class(self.app_class)
            if self.debug:
                self.flask_app = SocketIODebugger(self.flask_app,
                    evalex=True, namespace=SocketIONamespace)
            server = SocketIOServer((self.host, self.port), self.flask_app,
                resource='socket.io', policy_server=False)
            if self.debug:
                run_with_reloader(server.serve_forever)
            else:
                server.serve_forever()
        except KeyboardInterrupt:
            print '\rShutting down...'

    def socketio(self, path):
        try:
            socketio_manage(request.environ, {'/api': SocketIONamespace}, request)
        except:
            self.flask_app.logger.error('socket.io exception', exc_info=True)
        return Response()

    def index(self):
        return self.template
