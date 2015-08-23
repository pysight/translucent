# -*- coding: utf-8 -*_

import os
import six
import json
import logging
from tornado.web import RequestHandler, StaticFileHandler
from tornado.web import Application as WebApplication
from tornado.ioloop import IOLoop
from tornado import autoreload
from sockjs.tornado import SockJSRouter, SockJSConnection

from translucent.reactive import Context
from translucent.transpile import transpile_jsx, get_js_runtime

log = logging.getLogger('translucent')
log.addHandler(logging.NullHandler())


class WebHandler(RequestHandler):
    def initialize(self, title, transpile):
        self.title = title
        self.transpile = transpile

    def get(self):
        self.render('index.html', title=self.title or 'translucent', transpile=self.transpile)


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


class TextHandler(RequestHandler):
    def initialize(self, text):
        self.text = text

    def get(self):
        self.finish(self.text)


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


def get_code(path, transpile=None):
    if not os.path.isfile(path):
        raise OSError('file not found: {}'.format(path))
    code = open(path).read()
    if transpile is None:
        transpile = get_js_runtime() is not None
    else:
        transpile = bool(transpile)
    if transpile:
        code = transpile_jsx(code)
    return code, transpile


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
    def start(cls, script='index.js', title=None, stylesheet=None, debug=False, port=9999,
              transpile=None):
        log.debug('Application::start')

        cls.setup()

        root = os.path.dirname(__file__)
        router = SockJSRouter(cls, '/api')

        settings = {
            'static_path': os.path.join(root, 'static'),
            'template_path': os.path.join(root, 'templates'),
            'debug': debug
        }

        script = os.path.abspath(os.path.join(os.path.dirname(__file__), script))
        code, transpile = get_code(script, transpile=transpile)

        handlers = [
            ('/', WebHandler, {'title': title, 'transpile': transpile}),
            ('/index.js', TextHandler, {'text': code}),
            ('/index.css', FileHandler, {'path': stylesheet})
        ]
        handlers.extend(router.urls)

        app = WebApplication(handlers, **settings)
        app.listen(port)

        if debug and transpile:
            autoreload.watch(script)

        IOLoop.instance().start()
