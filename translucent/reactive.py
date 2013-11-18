# -*- coding: utf-8 -*-

import inspect
import re
import sys
import pandas as pd
from contextlib import contextmanager
from collections import defaultdict

from .utils import is_string


class UndefinedKey(Exception):

    def __init__(self, name=None):
        self.name = name


class ReactiveObject(object):

    def __init__(self, name):
        name_regex = r'^((_[_]+)|[a-zA-Z])[_a-zA-Z0-9]*$'
        if not is_string(name) or not re.match(name_regex, name):
            raise Exception('invalid reactive object name: "%s"' % name)
        self.name = name
        self.value = None
        self.fn = None
        self.invalidated = True
        self.parents = []
        self.children = []
        self.context = None
        self.exec_count = 0

    def invalidate(self):
        self.invalidated = True
        with self.context.log_block('%s.invalidate()', self.name):
            for child in self.children:
                child.invalidate()
                if child.is_observer():
                    if child not in self.context.flush_queue:
                        self.context.log('flush_queue.append(%s)', child.name)
                        self.context.flush_queue.append(child)
                    else:
                        self.context.log('%s in flush_queue', child.name)
            for parent in self.parents:
                parent.children = [child for child in parent.children if child != self]
        self.children = []

    def is_observer(self):
        return isinstance(self, ReactiveObserver)

    def is_value(self):
        return isinstance(self, ReactiveValue)

    def add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)
        if self not in parent.children:
            parent.children.append(self)

    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)
        if self not in child.parents:
            child.parents.append(self)


class ReactiveValue(ReactiveObject):

    def __init__(self, name, value):
        super(ReactiveValue, self).__init__(name)
        self.value = value

    def set_value(self, new_value):
        with self.context.log_block('%s.set_value(%r)', self.name, new_value):
            if self.value != new_value:
                self.invalidate()
            self.value = new_value
            self.context.flush()

    def get_value(self):
        self.invalidated = False
        return self.value


class ReactiveExpression(ReactiveObject):

    def __init__(self, name, fn):
        super(ReactiveExpression, self).__init__(name)
        self.fn = fn

    def get_value(self):
        if self.invalidated or self in self.context.running:
            try:
                self.context.running[0:0] = [self]
                self.invalidated = False
                with self.context.log_block('%s.run()', self.name):
                    self.value = self.fn(self.context.env)
            except UndefinedKey as e:
                self.context.log('=> UndefinedKey')
                self.invalidated = True
                raise e
            finally:
                self.context.running.remove(self)
                self.exec_count += 1
        return self.value


class ReactiveObserver(ReactiveObject):

    def __init__(self, name, fn):
        super(ReactiveObserver, self).__init__(name)
        self.fn = fn

    def run(self, *args):
        try:
            self.context.running[0:0] = [self]
            self.invalidated = False
            with self.context.log_block('%s.run()', self.name):
                self.value = self.fn(self.context.env)
        except UndefinedKey as e:
            self.context.log('=> UndefinedKey')
            self.context.pending[e.name].append(self)
        finally:
            self.context.running.remove(self)
            self.exec_count += 1


class ReactiveEnvironment(object):

    def __init__(self, context):
        self._context = context

    def __getattr__(self, name):
        if name != '_context':
            return self._context.get_value(name)
        else:
            return self.__dict__[name]

    def __getitem__(self, name):
        return self._context.get_value(name)

    def __setattr__(self, name, value):
        if name != '_context':
            self._context.set_value(name, value)
        else:
            self.__dict__[name] = value

    def __setitem__(self, name, value):
        self._context.set_value(name, value)

    def __contains__(self, name):
        return name in self._context


class ReactiveContext(object):

    def __init__(self, log=None):
        self.env = ReactiveEnvironment(self)
        self.objects = {}
        self.pending = defaultdict(list)
        self.flush_queue = []
        self.log_stream = None
        self.log_indent = 0
        self.running = []
        if log is True:
            self.start_log()
        elif log is not None:
            self.start_log(log)

    def start_log(self, stream=None):
        self.log_stream = stream or sys.stdout

    def stop_log(self):
        self.log_stream = None

    def log(self, fmt, *args):
        args = list(args)
        for i, arg in enumerate(args):
            if isinstance(arg, (pd.DataFrame, pd.Series)):
                args[i] = type(arg)
        args = tuple(args)
        if self.log_stream is not None:
            self.log_stream.write('  ' * self.log_indent + fmt % args + '\n')

    @contextmanager
    def log_block(self, fmt=None, *args):
        if fmt is not None:
            self.log(fmt, *args)
        self.log_indent += 1
        try:
            yield
        except Exception as e:
            raise e
        finally:
            self.log_indent -= 1

    def __contains__(self, name):
        return name in self.objects

    def __getitem__(self, name):
        return self.objects[name]

    def register(self, obj):
        self.objects[obj.name] = obj
        obj.context = self
        while self.pending[obj.name]:
            self.pending[obj.name].pop().run()
        return obj

    def get_caller(self):
        for frame in inspect.stack():
            caller = frame[0].f_locals.get('self', None)
            if isinstance(caller, ReactiveObject):
                return caller
        return None

    def get_value(self, name):
        if name not in self.objects:
            raise UndefinedKey(name)
        obj = self.objects[name]
        if obj.is_observer():
            raise Exception('cannot get the value of observer "%s"' % name)
        caller = self.get_caller()
        if caller is not None and caller != obj:
            caller.add_parent(obj)
        with self.log_block('get_value(%s)', name):
            value = obj.get_value()
        self.log('=> %r', value)
        return value

    def set_value(self, name, value, auto_add=False):
        if auto_add and name not in self.objects:
            return self.new_value(name, value)
        obj = self.objects[name]
        if not obj.is_value():
            raise Exception('"%s" is not a reactive value' % name)
        with self.log_block('set_value(%s, %r)', name, value):
            obj.set_value(value)

    def flush(self):
        if self.running:
            self.log('no flush (already running)')
            return
        with self.log_block('flush()'):
            while self.flush_queue:
                obj = self.flush_queue.pop()
                with self.log_block('flush_queue.pop(%s).run()', obj.name):
                    obj.run()
        if self.flush_queue:
            self.flush()

    def run(self):
        with self.log_block('run()'):
            [v.run() for v in self.objects.itervalues() if v.is_observer()]
            self.flush()

    def new_value(self, name, value):
        return self.register(ReactiveValue(name, value))

    def new_expression(self, name, fn):
        return self.register(ReactiveExpression(name, fn))

    def new_observer(self, name, fn):
        return self.register(ReactiveObserver(name, fn))

    def expression(self, name):
        def decorator(fn):
            return self.new_expression(name, fn)
        return decorator

    def observer(self, name):
        def decorator(fn):
            return self.new_observer(name, fn)
        return decorator
