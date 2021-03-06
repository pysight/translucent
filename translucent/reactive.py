# -*- coding: utf-8 -*-

__all__ = ('Value', 'Expression', 'Observer', 'Context')

import re
import sys
from contextlib import contextmanager
from collections import defaultdict
from joblib import hashing

from .utils import is_string


def _fast_hash(obj):
    """
    Returns hash of an arbitrary Python object.

    Works for numpy arrays, pandas objects, custom classes and functions. If an
    object doesn't support hashing natively, use md5-based ``joblib.hashing.hash()``,
    otherwise use the standard ``hash()`` function for the sake of performance.
    """
    try:
        return hash(obj)
    except:
        return hashing.hash(obj)


class UndefinedKey(Exception):

    """
    This exception is raised by a reactive environment upon an attempt to access
    a non-existing reactive object by name. The exception is propagated up the
    call stack; if it reaches an observer, the context will force this observer
    to run once a reactive object of a given name is bound to the context.

    Parameters
    ----------
    name : string
        Name of the reactive object that was accessed from the environment.
    """

    def __init__(self, name=None):
        super(UndefinedKey, self).__init__()
        self.name = name


class _Object(object):

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

    def invalidate(self):
        """
        Mark a reactive object as invalidated.
        """
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
        return isinstance(self, Value)

    def is_observer(self):
        return isinstance(self, Observer)

    def is_expression(self):
        return isinstance(self, Expression)

    def add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)
        if self not in parent.children:
            parent.children.append(self)


class Value(_Object):

    """
    Reactive value.
    """

    def __init__(self, name, value):
        super(Value, self).__init__(name)
        self.value = value
        self.hash = _fast_hash(value)

    def set_value(self, value):
        """
        Parameters
        ----------
        value : object
        """
        with self.context.log_block('%s.set_value(%s)', self.name,
                self.context._fmt_value(value)):
            new_hash = _fast_hash(value)
            if self.value != value or (self.context.safe and self.hash != new_hash):
                self.invalidate()
            self.value = value
            self.hash = new_hash
            self.context.flush()

    def get_value(self, isolate=False):
        """
        Parameters
        ----------
        isolate : bool (optional, default: False)
        """
        if not isolate:
            self.invalidated = False
        return self.value


class _Callable(_Object):

    def __init__(self, name, func):
        super(_Callable, self).__init__(name)
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


class Expression(_Callable):

    """
    Reactive expression.
    """

    __slots__ = ('memoized', '_cache', '_current_cache')

    def __init__(self, name, func):
        super(Expression, self).__init__(name, func)
        self.memoized = False
        self._cache = {}
        self._current_cache = {}

    def get_value(self, isolate=False):
        if self.invalidated or self.context._is_running(self):
            if self.memoized:
                env_hash = frozenset((name, obj.hash)
                    for name, obj in self.context._objects.iteritems()
                    if not obj.is_observer())
                for h in self._cache:
                    if h <= env_hash:
                        value = self._cache[h]
                        self.context.log('retrieving value from cache: %s -> %s',
                            self.name, self.context._fmt_value(value))
                        self.value = value
                        for name, _ in h:
                            self.add_parent(self.context[name])
                        return self.value
                self._current_cache = {}
            self.try_run(isolate=isolate)
            if self.memoized:
                key = frozenset(self._current_cache.items())
                if key not in self._cache:
                    self.context.log('updating cache: %s -> %s',
                        self.name, self.context._fmt_value(self.value))
                    self._cache[key] = self.value
        return self.value

    def _update_cache(self, name, value):
        if name not in self._current_cache:
            self._current_cache[name] = _fast_hash(value)


class Observer(_Callable):

    """
    Reactive observer.

    Parameters
    ----------
    name : string
        Name of the observer (alphanumeric characters and underscores only, cannot start with a
        single underscore or a digit).
    func : dict
        The function ``func(env)``

        Examples
        --------
        >>> obs = Observer('obs', lambda env: env.x + 1)
    """

    def __init__(self, name, func):
        super(Observer, self).__init__(name, func)

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


class Environment(object):

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


class Context(object):

    """
    The reactive context.

    Parameters
    ----------
    safe : bool (optional, default: `True`)
        Indicates whether the context should run in safe mode in which the integrity
        of hashed values is automatically checked after each run of a reactive
        expression or observer.
    log : bool, stream (optional)
        If a stream is passed, all of the activity within the context is logged
        to the stream. If set to `True`, enables verbose logging to the standard output.
    formatter : function (optional)
        If specified, all values will be first passed using this formatter when
        logging.
    """

    __slots__ = ('safe', 'env', '_objects', '_call_stack', '_pending', '_log_stream',
        '_log_indent', '_fmt_value', '_flush_queue')

    def __init__(self, safe=True, log=None, formatter=None):
        self.safe = safe
        self.env = Environment(self)

        self._objects = {}
        self._call_stack = []
        self._pending = defaultdict(list)
        self._log_stream = None
        self._log_indent = 0
        self._fmt_value = repr
        self._flush_queue = []

        if log is True:
            self.start_log(formatter=formatter)
        elif log is not None:
            self.start_log(log, formatter=formatter)

    def new_value(self, *args, **kwargs):
        """
        Create one or more reactive values and bind them to the context.

        Parameters
        ----------
        args : list
            ``name1, value1, name2, value2, ...``
        kwargs : dict
            ``{name1: value1, name2: value2, ...}``

        Examples
        --------
        >>> rc = Context()
        >>> a = rc.new_value(a=1)
        >>> b = rc.new_value('b', 2)
        >>> rc.new_value('c', 3, d=4, e=5)

        Returns
        -------
        obj : :class:`.Value` if only one name/value pair is passed, else `None`.

        Notes
        -----
        The name of a reactive value can contain any number of alphanumeric characters and
        underscore but it cannot start with a single underscore (although it may start
        with two or more) or a digit.

        Note that all observers that tried to access a reactive value by name (directly
        or indirectly via reactive expressions) before the value was bound to the context
        will **instantly** run right after it is created and bound.
        """
        return self._new_object(Value, *args, **kwargs)

    def new_expression(self, *args, **kwargs):
        """
        Create one or more reactive expressions and bind them to the context.

        A reactive expression wraps a function that accepts a
        :class:`.Environment` instance as an argument and returns a value.

        Parameters
        ----------
        args : list
            ``name1, func1, name2, func2, ...``
        kwargs : dict
            ``{name1: func1, name2: func2, ...}``

        Examples
        --------
        >>> from operator import attrgetter, itemgetter
        >>> rc = Context()
        >>> a = rc.new_value(a=1, b=2)
        >>> rc.new_expression(c=attrgetter('a'), d=itemgetter('b'))
        >>> e = rc.new_expression('c', lambda env: env.a + env.b)

        Returns
        -------
        obj : :class:`.Expression` if only one name/function pair is passed, else `None`.

        Notes
        -----
        The name of a reactive expression can contain any number of alphanumeric characters
        and underscore but it cannot start with a single underscore (although it may start
        with two or more) or a digit.
        """
        return self._new_object(Expression, *args, **kwargs)

    def new_observer(self, *args, **kwargs):
        """
        Create one or more reactive observers and bind them to the context.

        A reactive observer wraps a function that accepts a
        :class:`.Environment` instance as an argument and can
        optionally return a value (but is generally not expected to).

        Parameters
        ----------
        args : list
            ``name1, func1, name2, func2, ...``
        kwargs : dict
            ``{name1: func1, name2: func2, ...}``

        Examples
        --------
        >>> rc = Context()
        >>> a = rc.new_value(a=1, b=2)
        >>> func_c = lambda env: env.a
        >>> func_d = lambda env: env.b
        >>> rc.new_observer(c=func_c, d=func_d)
        >>> e = rc.new_observer('e', lambda env: env.a + env.b)

        Returns
        -------
        obj : :class:`.Observer` if only one name/function pair is passed, else `None`.

        Notes
        -----
        The name of a reactive observer can contain any number of alphanumeric characters
        and underscore but it cannot start with a single underscore (although it may start
        with two or more) or a digit.
        """
        return self._new_object(Observer, *args, **kwargs)

    def expression(self, name):
        """
        Decorator that creates a reactive expression and binds it to the context.

        Parameters
        ----------
        name : string
            Name of the reactive expression.

        Examples
        --------
        >>> rc = Context()
        >>> rc.new_value(a=1)
        >>> b = rc.expression('a')(lambda env: env.a)
        >>> @rc.expression('c')
        ... def c(env):
        ...     return env.b

        See Also
        --------
        new_expression
        """
        def decorator(func):
            return self.new_expression(name, func)
        return decorator

    def observer(self, name):
        """
        Decorator that creates a reactive observer and binds it to the context.

        Parameters
        ----------
        name : string
            Name of the reactive observer.

        Examples
        --------
        >>> rc = Context()
        >>> rc.new_value(a=1)
        >>> b = rc.observer('a')(lambda env: env.a)
        >>> @rc.observer('c')
        ... def c(env):
        ...     return env.b

        See Also
        --------
        new_observer
        """
        def decorator(func):
            return self.new_observer(name, func)
        return decorator

    def set_value(self, *args, **kwargs):
        """
        Assign values to one or more :class:`.Value` objects.

        After the value is set, all observers and expressions depending on this
        value are invalidated and the context is flushed (i.e. any observers that
        were invalidated are scheduled to run).

        Parameters
        ----------
        args : list
            ``name1, value1, name2, value2, ...``
        kwargs : dict
            ``{name1: value1, name2: value2, ...}``

        Notes
        -----
        If ``_auto_add=True`` keyword argument is provided, this function will
        create a reactive value and bind it to the context (instead of throwing
        an exception) when a reactive object cannot be found in the context by
        name.

        Examples
        --------
        >>> rc = Context()
        >>> rc.new_value(a=1)
        >>> rc.set_value('a', 2)
        >>> rc.set_value(b=3, _auto_add=True)
        """
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
            value = obj.get_value(isolate=isolate)
        if not isolate and caller and caller.is_expression() and caller.memoized:
            caller._update_cache(name, value)
        self.log('=> %s', self._fmt_value(value))
        return value

    def flush(self):
        """
        Flush the reactive context.

        All observers that were added to the flush queue due to invalidation will be
        instantly run.
        """
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
        """
        Forces all invalidated observers to run.

        If the context runs in safe mode, hash integrity will be verified before
        the observers are scheduled to run.
        """
        if self.safe:
            self._check_hash_integrity()
        with self.log_block('run()'):
            for obj in self._objects.itervalues():
                if obj.is_observer() and obj.invalidated:
                    obj.run()
            self.flush()

    def memoize(self, expr, enable=True):
        """
        Enable or disable memoization (caching) of a reactive expression. A cached
        expression internally stores its returned values associated with the sets of
        values (hashes, to be precise) of its dependencies; when invalidated, it
        will first do a cache lookup before propagating the invalidation state.

        Parameters
        ----------
        expr : string or :class:`.Expression`
            Reactive expression, can be specified by name or by reference.
        enable : bool (optional, default: `True`)
            Enable or disable memoization of a reactive expression.

        Examples
        --------
        >>> rc = Context()
        >>> rc.new_value(a=1)
        >>> b = rc.new_expression('b', lambda env: env.a)
        >>> rc.memoize('b')
        >>> assert b.memoized
        >>> rc.memoize(b, False)
        >>> assert not b.memoized
        """
        if isinstance(expr, Expression):
            expr.memoized = enable
        else:
            obj = self[expr]
            if obj.is_expression():
                obj.memoized = enable
            else:
                raise Exception('can only cache reactive expressions')

    def suspend(self, name):
        """
        Suspend a reactive observer.

        The observer will stop triggering context flushes when reactive expressions
        or values it is dependent on are invalidated. If the observer is already
        in the flush queue by the time this method is called, the next re-execution
        will still take place.

        Parameters
        ----------
        name : string
            Name of the observer.
        """
        obj = self[name]
        if not obj.is_observer():
            raise Exception('can only suspend observers')
        obj.suspend()

    def resume(self, name, run=False):
        """
        Resume a suspended reactive observer.

        Note that by default the observer is not re-run automatically when resumed
        even if it is invalidated. This behavior can be altered by setting `run`
        keyword argument to `False`.

        Parameters
        ----------
        name : string
            Name of the observer.
        run : bool (optional, default: `False`)
            If set to `True`, the observer will check its invalidation state after
            resuming and schedule itself to run if necessary.
        """
        obj = self[name]
        if not obj.is_observer():
            raise Exception('can only resume observers')
        obj.resume(run=run)

    def start_log(self, stream=None, formatter=None):
        self._fmt_value = formatter or repr
        self._log_stream = stream or sys.stdout
        if not hasattr(self._log_stream, 'write'):
            raise Exception('expected stream, got %r' % type(self._log_stream))

    def stop_log(self):
        """
        Reset the logging output stream and halt all logging.
        """
        self._log_stream = None

    def log(self, fmt, *args):
        if self._log_stream is not None:
            self._log_stream.write('  ' * self._log_indent + fmt % args + '\n')

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
        """
        Check if the context contains a reactive object with a given name.

        Parameters
        ----------
        name : string
            Name of a reactive object.

        Examples
        --------
        >>> rc = Context()
        >>> rc.new_value(a=1)
        >>> assert 'a' in rc and 'b' not in rc
        """
        return name in self._objects

    def __getitem__(self, name):
        """
        Retrieve a reference to a reactive object by name.

        Parameters
        ----------
        name : string
            Name of a reactive object.

        Examples
        --------
        >>> rc = Context()
        >>> a = rc.new_value(a=1)
        >>> assert rc['a'] == a
        """
        return self._objects[name]

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

    def _register_pending(self, name, observer):
        if observer not in self._pending[name]:
            self._pending[name].append(observer)

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
