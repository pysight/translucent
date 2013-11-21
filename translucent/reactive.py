# -*- coding: utf-8 -*-

import inspect
import re
import sys
from contextlib import contextmanager
from collections import defaultdict
from joblib import hashing

from .utils import is_string

__all__ = ('ReactiveValue', 'ReactiveExpression', 'ReactiveObserver', 'ReactiveContext')


class UndefinedKey(Exception):

    def __init__(self, name=None):
        super(UndefinedKey, self).__init__()
        self.name = name


class ReactiveObject(object):

    __slots__ = ('name', 'value', 'hash', 'fn', 'invalidated', 'parents', 'children',
        'context', 'exec_count', 'suspended')

    def __init__(self, name):
        name_regex = r'^((_[_]+)|[a-zA-Z])[_a-zA-Z0-9]*$'
        if not is_string(name) or not re.match(name_regex, name):
            raise Exception('invalid reactive object name: "%s"' % name)
        self.name = name
        self.value = None
        self.hash = hashing.hash(self.value)
        self.fn = None
        self.invalidated = True
        self.parents = []
        self.children = []
        self.context = None
        self.exec_count = 0
        self.suspended = False

    def invalidate(self):
        self.invalidated = True
        if self.is_observer() and not self.suspended:
            if self not in self.context._flush_queue:
                self.context.log('flush_queue.append(%s)', self.name)
                self.context._flush_queue.append(self)
            else:
                self.context.log('%s in flush_queue', self.name)
        with self.context.log_block('%s.invalidate()', self.name):
            for child in self.children:
                child.invalidate()
            for parent in self.parents:
                parent.children = [child for child in parent.children if child != self]
        self.children = []

    def is_value(self):
        return isinstance(self, ReactiveValue)

    def is_observer(self):
        return isinstance(self, ReactiveObserver)

    def is_expression(self):
        return isinstance(self, ReactiveExpression)

    def add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)
        if self not in parent.children:
            parent.children.append(self)


class ReactiveValue(ReactiveObject):

    def __init__(self, name, value):
        super(ReactiveValue, self).__init__(name)
        self.value = value
        self.hash = hashing.hash(value)

    def set_value(self, new_value):
        with self.context.log_block('%s.set_value(%s)', self.name,
                self.context._fmt_value(new_value)):
            if self.context.safe:
                new_hash = hashing.hash(new_value)
            if self.value != new_value or (self.context.safe and self.hash != new_hash):
                self.invalidate()
            self.value = new_value
            if self.context.safe:
                self.hash = new_hash
            self.context.flush()

    def get_value(self, isolate=False):
        if not isolate:
            self.invalidated = False
        return self.value


class _ReactiveCallable(ReactiveObject):

    def __init__(self, name, fn):
        super(_ReactiveCallable, self).__init__(name)
        if not callable(fn):
            raise Exception('fn in expression "%s" must be a callable' % name)
        self.fn = fn

    def try_run(self, isolate=False):
        try:
            self.context._push_callable(self)
            self.invalidated = False
            with self.context.log_block('%s.run()', self.name):
                self.value = self.fn(self.context.env)
                if self.context.safe:
                    self.hash = hashing.hash(self.value)
                    self.context._check_hash_integrity()
        except UndefinedKey as e:
            self.context.log('=> UndefinedKey')
            self.invalidated = True
            raise e
        finally:
            self.context._pop_callable(self)
            self.exec_count += 1


class ReactiveExpression(_ReactiveCallable):

    def __init__(self, name, fn):
        super(ReactiveExpression, self).__init__(name, fn)

    def get_value(self, isolate=False):
        if self.invalidated or self.context._is_running(self):
            self.try_run(isolate=isolate)
        return self.value


class ReactiveObserver(_ReactiveCallable):

    def __init__(self, name, fn):
        super(ReactiveObserver, self).__init__(name, fn)

    def run(self):
        try:
            self.try_run()
        except UndefinedKey as e:
            self.context._register_pending(e.name, self)

    def suspend(self):
        self.context.log('%s.suspend()', self.name)
        self.suspended = True

    def resume(self, run=False):
        self.context.log('%s.resume()', self.name)
        if self.suspended and self.invalidated and run:
            self.suspended = False
            self.run()
        else:
            self.suspended = False


class ReactiveEnvironment(object):

    def __init__(self, context, isolate=False):
        self._context = context
        self._isolate = isolate

    def __getattr__(self, key):
        return self._context.get_value(key, self._isolate)

    def __getitem__(self, key):
        if key == slice(None, None, None):
            if not self._isolate:
                return self.__class__(self._context, isolate=True)
            else:
                return self
        elif key is Ellipsis:
            return self._isolate_block()
        return self._context.get_value(key, self._isolate)

    def __setattr__(self, key, value):
        if key not in ('_context', '_isolate'):
            self._context.set_value(key, value)
        else:
            self.__dict__[key] = value

    def __setitem__(self, key, value):
        self._context.set_value(key, value)

    def __contains__(self, key):
        return key in self._context

    def __invert__(self):
        return self._isolate_block()

    @contextmanager
    def _isolate_block(self):
        self._isolate = True
        yield self
        self._isolate = False


class ReactiveContext(object):

    __slots__ = ('safe', 'env', '_objects', '_running', '_pending', '_log_stream',
        '_log_indent', '_fmt_value', '_flush_queue')

    def __init__(self, safe=True, log=None, formatter=None):
        self.safe = safe
        self.env = ReactiveEnvironment(self)

        self._objects = {}
        self._running = []
        self._pending = defaultdict(list)
        self._log_stream = None
        self._log_indent = 0
        self._fmt_value = formatter or repr
        self._flush_queue = []

        if log is True:
            self.start_log()
        elif log is not None:
            self.start_log(log)

    def new_value(self, *args, **kwargs):
        return self._new_object(ReactiveValue, *args, **kwargs)

    def new_expression(self, *args, **kwargs):
        return self._new_object(ReactiveExpression, *args, **kwargs)

    def new_observer(self, *args, **kwargs):
        return self._new_object(ReactiveObserver, *args, **kwargs)

    def expression(self, name):
        def decorator(fn):
            return self.new_expression(name, fn)
        return decorator

    def observer(self, name):
        def decorator(fn):
            return self.new_observer(name, fn)
        return decorator

    def set_value(self, *args, **kwargs):
        auto_add = kwargs.pop('_auto_add', False)
        for k, v in self._get_args(ReactiveValue, *args, **kwargs):
            if auto_add and k not in self:
                return self.new_value(k, v)
            obj = self[k]
            if not obj.is_value():
                raise Exception('"%s" is not a reactive value' % k)
            with self.log_block('set_value(%s, %r)', k, self._fmt_value(v)):
                obj.set_value(v)

    def run(self):
        with self.log_block('run()'):
            for obj in self._objects.itervalues():
                if obj.is_observer() and obj.invalidated:
                    obj.run()
            self.flush()

    def suspend(self, key):
        obj = self[key]
        if not obj.is_observer():
            raise Exception('can only suspend observers')
        obj.suspend()

    def resume(self, key, run=False):
        obj = self[key]
        if not obj.is_observer():
            raise Exception('can only resume observers')
        obj.resume(run=run)

    def __contains__(self, name):
        return name in self._objects

    def __getitem__(self, name):
        return self._objects[name]

    def __len__(self):
        return len(self._objects)

    def start_log(self, stream=None, formatter=None):
        self._fmt_value = formatter or repr
        self._log_stream = stream or sys.stdout

    def stop_log(self):
        self._log_stream = None

    def log(self, fmt, *args):
        if self._log_stream is not None:
            self._log_stream.write('  ' * self._log_indent + fmt % args + '\n')

    @contextmanager
    def log_block(self, fmt=None, *args):
        if fmt is not None:
            self.log(fmt, *args)
        self._log_indent += 1
        try:
            yield
        except Exception as e:
            raise e
        finally:
            self._log_indent -= 1

    def get_value(self, name, isolate=False):
        if name not in self:
            raise UndefinedKey(name)
        obj = self[name]
        if obj.is_observer():
            raise Exception('cannot get the value of observer "%s"' % name)
        if not isolate:
            caller = self._get_caller()
            if caller is not None and caller != obj:
                caller.add_parent(obj)
        with self.log_block('get_value(%s)%s', name, ' [isolated]' * isolate):
            value = obj.get_value(isolate=True)
        self.log('=> %s', self._fmt_value(value))
        return value

    def flush(self):
        if self._running:
            self.log('no flush (already running)')
            return
        with self.log_block('flush()'):
            while self._flush_queue:
                obj = self._flush_queue.pop()
                with self.log_block('flush_queue.pop(%s).run()', obj.name):
                    obj.run()
        if self._flush_queue:
            self.flush()

    def _get_caller(self):
        for frame in inspect.stack():
            caller = frame[0].f_locals.get('self', None)
            if isinstance(caller, ReactiveObject):
                return caller
        return None

    def _check_hash_integrity(self):
        if self.safe:
            for obj in self._objects.itervalues():
                if hashing.hash(obj.value) != obj.hash:
                    if obj.is_value():
                        self.log('outdated hash detected for %s', obj.name)
                        obj.set_value(obj.value)
                    else:
                        raise Exception('non-value object value mutated')

    def _register(self, obj):
        self._objects[obj.name] = obj
        obj.context = self
        while self._pending[obj.name]:
            self._pending[obj.name].pop().run()
        return obj

    def _new_object(self, cls, *args, **kwargs):
        result = []
        for k, v in self._get_args(cls, *args, **kwargs):
            result.append(self._register(cls(k, v)))
        if len(result) is 1:
            return result[0]

    def _register_pending(self, value_key, observer):
        if observer not in self._pending[value_key]:
            self._pending[value_key].append(observer)

    def _push_callable(self, obj):
        self._running[0:0] = [obj]

    def _pop_callable(self, obj):
        self._running.remove(obj)

    def _is_running(self, obj):
        return obj in self._running

    @staticmethod
    def _get_args(cls, *args, **kwargs):
        if issubclass(cls, (ReactiveExpression, ReactiveObserver)):
            kind = 'fn/value'
        else:
            kind = 'name/value'
        if not args and not kwargs:
            raise Exception('at least one %s pair or kwargs must be provided' % kind)
        if len(args) % 2:
            raise Exception('args length must be divisible by 2 (list of %s pairs)' % kind)
        duplicates = sorted(set(args[0::2]) & set(kwargs.iterkeys()))
        if duplicates:
            raise Exception('duplicate arguments passed: %r' % duplicates)
        result = dict(zip(args[0::2], args[1::2]))
        result.update(kwargs)
        return result.items()
