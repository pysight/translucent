# -*- coding: utf-8 -*-

__all__ = ('ReactiveValue', 'ReactiveExpression', 'ReactiveObserver', 'ReactiveContext')

import re
import sys
from contextlib import contextmanager
from collections import defaultdict
from joblib import hashing

from .utils import is_string


def _fast_hash(x):
    try:
        return hash(x)
    except:
        return hashing.hash(x)


class UndefinedKey(Exception):

    def __init__(self, name=None):
        super(UndefinedKey, self).__init__()
        self.name = name


class ReactiveObject(object):

    __slots__ = ('name', 'value', 'hash', 'func', 'invalidated', 'parents', 'children',
        'context', 'exec_count', 'suspended')

    def __init__(self, name):
        name_regex = r'^((_[_]+)|[a-zA-Z])[_a-zA-Z0-9]*$'
        if not is_string(name) or not re.match(name_regex, name):
            raise Exception('invalid reactive object name: "%s"' % name)
        self.name = name
        self.value = None
        self.hash = _fast_hash(self.value)
        self.func = None
        self.invalidated = True
        self.parents = []
        self.children = []
        self.context = None
        self.exec_count = 0
        self.suspended = False
        self.accessed = []

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
        self.hash = _fast_hash(value)

    def set_value(self, new_value):
        with self.context.log_block('%s.set_value(%s)', self.name,
                self.context._fmt_value(new_value)):
            new_hash = _fast_hash(new_value)
            if self.value != new_value or (self.context.safe and self.hash != new_hash):
                self.invalidate()
            self.value = new_value
            self.hash = new_hash
            self.context.flush()

    def get_value(self, isolate=False):
        if not isolate:
            self.invalidated = False
        return self.value


class _ReactiveCallable(ReactiveObject):

    def __init__(self, name, func):
        super(_ReactiveCallable, self).__init__(name)
        if not callable(func):
            raise Exception('func in expression "%s" must be a callable' % name)
        self.func = func

    def try_run(self, isolate=False):
        try:
            self.context._push_call_stack(self)
            self.invalidated = False
            with self.context.log_block('%s.run()', self.name):
                self.value = self.func(self.context.env)
                self.hash = _fast_hash(self.value)
                if self.context.safe and self.parents:
                    self.context._check_hash_integrity(self.parents)
        except UndefinedKey as e:
            self.context.log('=> UndefinedKey')
            self.invalidated = True
            raise e
        finally:
            self.context._pop_call_stack(self)
            self.exec_count += 1


class ReactiveExpression(_ReactiveCallable):

    def __init__(self, name, func):
        super(ReactiveExpression, self).__init__(name, func)
        self.cached = False
        self.cache = {}
        self.current_cache = {}

    def get_value(self, isolate=False):
        if self.invalidated or self.context._is_running(self):
            if self.cached:
                env_hash = frozenset((name, obj.hash)
                    for name, obj in self.context._objects.iteritems()
                    if not obj.is_observer())
                for h in self.cache:
                    if h <= env_hash:
                        value = self.cache[h]
                        self.context.log('retrieving value from cache: %s -> %s',
                            self.name, self.context._fmt_value(value))
                        self.value = value
                        for name, _ in h:
                            self.add_parent(self.context[name])
                        return self.value
                self.current_cache = {}
            self.try_run(isolate=isolate)
            key = frozenset(self.current_cache.items())
            if key not in self.cache:
                self.context.log('updating cache: %s -> %s',
                    self.name, self.context._fmt_value(self.value))
                self.cache[key] = self.value
        return self.value

    def update_cache(self, name, value):
        if name not in self.current_cache:
            self.current_cache[name] = _fast_hash(value)


class ReactiveObserver(_ReactiveCallable):

    def __init__(self, name, func):
        super(ReactiveObserver, self).__init__(name, func)

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

    __slots__ = ('safe', 'env', '_objects', '_call_stack', '_pending', '_log_stream',
        '_log_indent', '_fmt_value', '_flush_queue')

    def __init__(self, safe=True, log=None, formatter=None):
        self.safe = safe
        self.env = ReactiveEnvironment(self)

        self._objects = {}
        self._call_stack = []
        self._pending = defaultdict(list)
        self._log_stream = None
        self._log_indent = 0
        self._flush_queue = []
        self._fmt_value = repr

        if log is True:
            self.start_log(formatter=formatter)
        elif log is not None:
            self.start_log(log, formatter=formatter)

    def new_value(self, *args, **kwargs):
        return self._new_object(ReactiveValue, *args, **kwargs)

    def new_expression(self, *args, **kwargs):
        return self._new_object(ReactiveExpression, *args, **kwargs)

    def new_observer(self, *args, **kwargs):
        return self._new_object(ReactiveObserver, *args, **kwargs)

    def expression(self, name):
        def decorator(func):
            return self.new_expression(name, func)
        return decorator

    def observer(self, name):
        def decorator(func):
            return self.new_observer(name, func)
        return decorator

    def set_value(self, *args, **kwargs):
        auto_add = kwargs.pop('_auto_add', False)
        for k, v in self._get_args(*args, **kwargs):
            if auto_add and k not in self:
                return self.new_value(k, v)
            obj = self[k]
            if not obj.is_value():
                raise Exception('"%s" is not a reactive value' % k)
            with self.log_block('set_value(%s, %r)', k, self._fmt_value(v)):
                obj.set_value(v)

    def get_value(self, name, isolate=False):
        if name not in self:
            raise UndefinedKey(name)
        obj = self[name]
        if obj.is_observer():
            raise Exception('cannot get the value of observer "%s"' % name)
        if not isolate:
            caller = self._get_caller()
            if caller is not None:
                if caller != obj:
                    caller.add_parent(obj)
                else:
                    self.log('[called from outside the context]')
        with self.log_block('get_value(%s)%s', name, ' [isolated]' * isolate):
            value = obj.get_value(isolate=True)
        if not isolate and caller and caller.is_expression() and caller.cached:
            caller.update_cache(name, value)
        self.log('=> %s', self._fmt_value(value))
        return value

    def flush(self):
        if self._call_stack:
            self.log('no flush (already running)')
        else:
            with self.log_block('flush()'):
                while self._flush_queue:
                    obj = self._flush_queue.pop()
                    with self.log_block('flush_queue.pop(%s).run()', obj.name):
                        obj.run()
            if self._flush_queue:
                self.flush()

    def run(self):
        if self.safe:
            self._check_hash_integrity()
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

    def start_log(self, stream=None, formatter=None):
        self._fmt_value = formatter or repr
        self._log_stream = stream or sys.stdout

    def stop_log(self):
        self._log_stream = None

    def log(self, fmt, *args):
        if self._log_stream is not None:
            self._log_stream.write('  ' * self._log_indent + fmt % args + '\n')

    def cache(self, expr, cached=True):
        if isinstance(expr, ReactiveExpression):
            expr.cached = cached
        else:
            obj = self[expr]
            if obj.is_expression():
                obj.cached = cached
            else:
                raise Exception('can only cache reactive expressions')

    @contextmanager
    def log_block(self, fmt=None, *args):
        if self._log_stream is None:
            yield
        else:
            if fmt is not None:
                self.log(fmt, *args)
            self._log_indent += 1
            try:
                yield
            except Exception as e:
                raise e
            finally:
                self._log_indent -= 1

    def __contains__(self, name):
        return name in self._objects

    def __getitem__(self, name):
        return self._objects[name]

    def __len__(self):
        return len(self._objects)

    def _check_hash_integrity(self, accessed=None):
        if self.safe:
            objects = accessed or self._objects.values()
            for obj in objects:
                if obj.is_value():
                    if _fast_hash(obj.value) != obj.hash:
                        self.log('outdated hash detected for %s', obj.name)
                        obj.set_value(obj.value)
            for obj in objects:
                if not obj.is_value():
                    if not obj.invalidated and _fast_hash(obj.value) != obj.hash:
                        raise Exception('non-value object mutated: %s' % obj.name)

    def _register(self, obj):
        self._objects[obj.name] = obj
        obj.context = self
        while self._pending[obj.name]:
            self._pending[obj.name].pop().run()
        return obj

    def _new_object(self, cls, *args, **kwargs):
        result = []
        for k, v in self._get_args(*args, **kwargs):
            result.append(self._register(cls(k, v)))
        if len(result) is 1:
            return result[0]

    def _register_pending(self, value_key, observer):
        if observer not in self._pending[value_key]:
            self._pending[value_key].append(observer)

    def _push_call_stack(self, obj):
        self._call_stack[0:0] = [obj]

    def _pop_call_stack(self, obj):
        self._call_stack.remove(obj)

    def _is_running(self, obj):
        return obj in self._call_stack

    def _get_caller(self):
        return None if not self._call_stack else self._call_stack[0]

    @staticmethod
    def _get_args(*args, **kwargs):
        if not args and not kwargs:
            raise Exception('at least one pair or kwargs must be provided')
        if len(args) % 2:
            raise Exception('args length must be divisible by 2 (list of pairs)')
        duplicates = sorted(set(args[0::2]) & set(kwargs.iterkeys()))
        if duplicates:
            raise Exception('duplicate arguments passed: %r' % duplicates)
        result = dict(zip(args[0::2], args[1::2]))
        result.update(kwargs)
        return result.items()
