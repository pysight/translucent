# -*- coding: utf-8 -*-

import blinker
import inspect


class UndefinedKey(Exception):

    def __init__(self, name=None):
        self.name = name


class ReactiveObject(object):

    def __init__(self, name):
        self.name = name
        self.value = None
        self.fn = None
        self.invalidated = True
        self.parents = []
        self.children = []
        self.env = None

    def invalidate(self):
        self.invalidated = True
        for child in self.children:
            child.invalidate()
            if child.is_observer():
                self.env._on_flush.connect(child.run)
        for parent in self.parents:
            parent.children = [child for child in parent.children if child != self]
        self.children = []

    def set_env(self, env):
        self.env = env

    def is_observer(self):
        return False

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

    def __init__(self, name):
        super(ReactiveValue, self).__init__(name)

    def set_value(self, new_value):
        print 'ro.set_value():', self.name, '->', new_value
        if self.value != new_value:
            self.invalidate()
        self.value = new_value
        self.env._flush()

    def get_value(self):
        print 'rv.get_value():', self.name
        self.invalidated = False
        return self.value


class ReactiveExpression(ReactiveObject):

    def __init__(self, name, fn):
        super(ReactiveExpression, self).__init__(name)
        self.fn = fn

    def get_value(self):
        print 're.get_value():', self.name
        if self.invalidated:
            print '  -> dirty, running function'
            self.value = self.fn(self.env)
            print '  -> clean'
            self.invalidated = False
        return self.value


class ReactiveObserver(ReactiveObject):

    def __init__(self, name, fn):
        super(ReactiveObserver, self).__init__(name)
        self.fn = fn

    def is_observer(self):
        return True

    def run(self, *args):
        print 'ro.run():', self.name
        try:
            self.fn(self.env)
            self.invalidated = False
        except UndefinedKey as e:
            if e.name not in self.env._pending:
                self.env._pending[e.name] = []
            self.env._pending[e.name].append(self)


class ReactiveEnvironment(object):

    def __init__(self):
        self._objects = {}
        self._on_flush = blinker.Signal()
        self._pending = {}

    def _flush(self):
        self._on_flush.send(self)
        self._on_flush = blinker.Signal()

    def _register(self, obj):
        self._objects[obj.name] = obj
        obj.set_env(self)
        if obj.name in self._pending:
            pending = self._pending[obj.name]
            while pending:
                pending.pop().run()
            del self._pending[obj.name]
        return obj

    def _get_caller(self):
        for frame in inspect.stack():
            caller = frame[0].f_locals.get('self', None)
            if isinstance(caller, ReactiveObject):
                return caller
        return None

    def _get_value(self, name):
        print 'env._get_value():', name
        if name not in self._objects:
            print '  -> undefined'
            raise UndefinedKey(name)
        obj = self._objects[name]
        if obj.is_observer():
            raise TypeError('cannot get the value of observer "%s"' % name)
        caller = self._get_caller()
        if caller is not None:
            caller.add_parent(obj)
        return obj.get_value()

    def __getattr__(self, name):
        return self._get_value(name)

    def __getitem__(self, name):
        return self._get_value(name)

    def __contains__(self, name):
        return name in self._objects


class ReactiveContext(object):

    def __init__(self):
        self.env = ReactiveEnvironment()

    def __contains__(self, name):
        return name in self.env

    def __setitem__(self, name, value):
        self.env._objects[name].set_value(value)

    def run(self):
        for k, v in self.env._objects.iteritems():
            if isinstance(v, ReactiveObserver):
                v.run()

    def value(self, name):
        obj = self.env._register(ReactiveValue(name))
        return obj

    def expression(self, name, fn=None):
        def new_fn(fn):
            return self.env._register(ReactiveExpression(name, fn))
        return new_fn if fn is None else new_fn(fn)

    def observer(self, name, fn=None):
        def new_fn(fn):
            return self.env._register(ReactiveObserver(name, fn))
        return new_fn if fn is None else new_fn(fn)
