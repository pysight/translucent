# -*- coding: utf-8 -*_

import os
import six
import json
import logging
from tornado.web import RequestHandler, StaticFileHandler
from tornado.web import Application as WebApplication
from tornado.ioloop import IOLoop
from sockjs.tornado import SockJSRouter, SockJSConnection

from translucent.reactive import Context

log = logging.getLogger('translucent')
log.addHandler(logging.NullHandler())


class WebHandler(RequestHandler):
    def initialize(self, title):
        self.title = title

    def get(self):
        self.render('index.html', title=self.title or 'translucent')


class FileHandler(StaticFileHandler):
    def initialize(self, path):
        if path is None:
            self.absolute_path = None
        else:
            self.absolute_path = os.path.abspath(os.path.expanduser(path))
            self.root, self.filename = os.path.split(self.absolute_path)

    def get(self, path=None, include_body=True):
        if self.absolute_path is None:
            self.finish('')
        else:
            return super(FileHandler, self).get(self.filename, include_body)


def reactive(fn):
    fn.__reactive__ = True
    return fn


def shared(fn):
    fn.__shared__ = True
    return fn


class ApplicationMeta(type):
    def __new__(meta, clsname, bases, clsdict):
        clsdict['_reactive'] = []
        clsdict['_shared'] = []
        for name, fn in clsdict.items():
            if callable(fn):
                if hasattr(fn, '__reactive__') and fn.__reactive__:
                    clsdict['_reactive'].append(name)
                elif hasattr(fn, '__shared__') and fn.__shared__:
                    clsdict['_reactive'].append(name)
                    clsdict['_shared'].append(name)
        return super(ApplicationMeta, meta).__new__(meta, clsname, bases, clsdict)


class Application(six.with_metaclass(ApplicationMeta, SockJSConnection)):
    def initialize():
        pass

    @classmethod
    def setup(cls):
        pass

    def __init__(self, session):
        super(Application, self).__init__(session)

    def _init_context(self):
        self.context = Context()
        for name in self._reactive:
            self.context.new_expression(name, getattr(self, name))
            if name in self._shared:
                self._add_observer(name)

    def _add_observer(self, name):
        def observer(env):
            func = getattr(self, name)
            self.send('value', {'key': name, 'value': func(env)})
        self.context.new_observer('__' + name, observer)

    def send(self, kind, data=None):
        log.debug('Application::send [{}] {}'.format(kind, type(data)))
        super(Application, self).send(json.dumps({'kind': kind, 'data': data}))

    def on_open(self, info):
        log.debug('Application::on_open')
        self._init_context()
        self.initialize()
        self.context.run()
        self.send('ready')

    def on_message(self, msg):
        msg = json.loads(msg)
        kind, data = msg['kind'], msg['data']
        log.debug('Application::on_message [{}] {!r}'.format(kind, data))
        if kind == 'value':
            self.context.set_value(data['key'], data['value'])

    def on_close(self):
        log.debug('Application::on_close')

    @classmethod
    def start(cls, script, title=None, stylesheet=None, debug=False, port=9999):
        log.debug('Application::start')

        cls.setup()

        root = os.path.dirname(__file__)
        router = SockJSRouter(cls, '/api')

        settings = {
            'static_path': os.path.join(root, 'static'),
            'template_path': os.path.join(root, 'templates'),
            'debug': debug
        }

        handlers = [
            ('/', WebHandler, {'title': title}),
            ('/index.js', FileHandler, {'path': script}),
            ('/index.css', FileHandler, {'path': stylesheet})
        ]
        handlers.extend(router.urls)

        app = WebApplication(handlers, **settings)
        app.listen(port)

        IOLoop.instance().start()