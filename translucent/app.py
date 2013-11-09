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

"""

ReactiveValue: inputs from AngularJS

    if modified on client side, get sent from client via sockets

    if modified on server side, get sent to client first and then see what happens

1.  App.on_init() is called

    can modify any reactive values

2.  recv_connect() on server side and on_connect() on client side happen

    the server has to send reactive values first, then retrieve the environment


"""


class App(object):

    def __init__(self):
        SocketIONamespace._on_env_init.connect(self.on_env_init)
        SocketIONamespace._on_value_change.connect(self.on_value_change)
        SocketIONamespace._on_connect.connect(self.on_connect)
        self.context = ReactiveContext()

    def on_env_init(self, sender, **kwargs):
        env = kwargs['env']
        print 'app:', env

    def on_value_change(self, sender, **kwargs):
        key, value = kwargs['key'], kwargs['value']
        print 'app:', key, value

    def set(self, name, value):
        if name not in self.context:
            self.context.value(name)
        self.context[name] = value

    def on_connect(self, sender):
        for key, obj in self.context.env._objects.iteritems():
            value = obj.get_value()
            print key, value
            self.send_value(key, value)

    def send_value(self, key, value):
        SocketIONamespace._on_send_value.send(self, key=key, value=value)

    def on_init(self):
        pass


class SocketIONamespace(BaseNamespace):

    _on_env_init = Signal()
    _on_value_change = Signal()
    _on_connect = Signal()
    _on_send_value = Signal()

    def __init__(self, *args, **kwargs):
        super(SocketIONamespace, self).__init__(*args, **kwargs)
        self._on_send_value.connect(self.send_value)

    def send_value(self, sender, **kwargs):
        self.emit('send_value', {'key': kwargs['key'], 'value': kwargs['value']})

    def on_value_change(self, data):
        self._on_value_change.send(self, key=data['key'], value=data['value'])

    def on_env_init(self, env):
        self._on_env_init.send(self, env=env)

    def recv_connect(self):
        print 'got connection'
        self.emit('hello')
        self._on_connect.send(self)

    def recv_disconnect(self):
        self.disconnect(silent=True)


class Server(object):

    def __init__(self, app, ui, host='127.0.0.1', port=5000, debug=True):
        if isinstance(app, App):
            self.app = app
            print 'Initializing the app...'
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
        self.debug = debug
        self.flask_app.debug = debug
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
