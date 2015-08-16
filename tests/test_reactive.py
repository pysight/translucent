# -*- coding: utf-8

import sys
from six.moves import StringIO
from pytest import raises

from translucent.reactive import UndefinedKey, Context, Value, Expression, Observer


def test_object_names():
    raises(Exception, Value, '_', None)
    raises(Exception, Value, '123name', 1)
    raises(Exception, Value, '_name123', None)
    raises(Exception, Value, '$1', None)
    assert Value('__name', 1).name == '__name'
    assert Value('__1', None).name == '__1'


def test_object_types():
    v = Value('v', None)
    e = Expression('e', id)
    o = Observer('o', id)

    assert not v.is_observer()
    assert not e.is_observer()
    assert o.is_observer()

    assert v.is_value()
    assert not e.is_value()
    assert not o.is_value()

    assert not v.is_expression()
    assert e.is_expression()
    assert not o.is_expression()


def test_constructors():
    rc = Context

    assert rc().new_value(a=1, b=2) is None
    assert rc().new_value('a', 1, 'b', 2) is None
    assert rc().new_value('a', 1, b=2) is None
    assert rc().new_value('a', 1, b=2) is None
    raises(Exception, lambda: rc().new_value('a', 1, b=2)['b'])

    raises(Exception, rc().new_value)
    raises(Exception, rc().new_value, 'a')
    raises(Exception, rc().new_value, 'a', 1, 'b', c=2)
    raises(Exception, rc().new_value, 'a', 1, a=2)

    assert rc().new_value('a', 1).name == 'a'
    assert rc().new_value(a=1).name == 'a'
    assert rc().new_value(a=1).is_value()


def test_decorators():
    rc = Context()
    rc.new_value(a=1)

    @rc.expression('b')
    def b(env):
        return env.a + 1

    @rc.observer('c')
    def c(env):
        return env.b + 1

    rc.run()
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1
    assert rc['c'].value is 3

    raises(Exception, rc.expression, 'hello', 'world')
    raises(Exception, rc.expression('hello'), 'world')

    raises(Exception, rc.observer, 'hello', 'world')
    raises(Exception, rc.observer('hello'), 'world')


def test_undefined_key():
    try:
        raise UndefinedKey('a')
    except UndefinedKey as e:
        assert e.name == 'a'

    rc = Context()
    rc.new_expression('b', lambda env: env.a + 1)
    rc.new_observer('c', lambda env: env.b + 1)
    raises(Exception, lambda: rc['a'])

    rc.run()
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1

    rc.new_value(a=1)
    assert rc['b'].exec_count is 2
    assert rc['c'].exec_count is 2
    assert rc['c'].value is 3


def test_environment():
    rc = Context()
    assert rc.env._context is rc
    assert not rc.env._isolate
    raises(UndefinedKey, lambda: rc.env.a)
    raises(UndefinedKey, lambda: rc.env['a'])

    a = rc.new_value(a=1)
    assert 'a' in rc.env
    rc.env['a'] += 1
    assert a.get_value() is 2

    assert rc.env[:]._context is rc
    assert rc.env[:]._isolate
    assert rc.env[:][:]._isolate


def test_set_same_value():
    rc = Context()
    rc.new_value(a=1)
    rc.new_observer('b', lambda env: env.a)

    rc.run()
    assert rc['b'].exec_count is 1

    rc.set_value(a=1)
    assert rc['b'].exec_count is 1


def test_overreactivity_1():
    rc = Context()
    rc.new_value(v=1)
    rc.new_expression('a', lambda env: env.v)
    rc.new_expression('b', lambda env: env.a + env.v)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1

    rc.set_value(v=11)
    assert rc['b'].exec_count is 2
    assert rc['c'].exec_count is 2


def test_overreactivity_2():
    rc = Context()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.b * env.a)
    rc.new_observer('d', lambda env: env.b * env.a)

    rc.run()
    assert rc['c'].value is 6
    assert rc['d'].value is 6
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1
    assert rc['d'].exec_count is 1

    rc.set_value(a=2)
    assert rc['c'].value is 14
    assert rc['d'].value is 14
    assert rc['b'].exec_count is 2
    assert rc['c'].exec_count is 2
    assert rc['d'].exec_count is 2


def test_order_of_evaluation():
    rc = Context()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.a * env.b)

    rc.run()
    assert rc['c'].value is 6
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1

    rc.set_value(a=2)
    assert rc['c'].value is 14
    assert rc['b'].exec_count is 2
    assert rc['c'].exec_count is 2

    rc = Context()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.b * env.a)

    rc.run()
    assert rc['c'].value is 6
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1

    rc.set_value(a=2)
    assert rc['c'].value is 14
    assert rc['b'].exec_count is 2
    assert rc['c'].exec_count is 2


class TestRecursion(object):
    def setup(self):
        self.rc = Context()
        self.rc.new_value(a=3)
        self.rc.new_observer('c', lambda env: env.b)

    def fn_circular(self, env):
        if env.a is 0:
            return 0
        env.a -= 1
        return env.a

    def fn_recursive(self, env):
        if env.a is 0:
            return 0
        env.a -= 1
        return env.b

    def fn_nonreactive(self, env):
        if self.a is 0:
            return 0
        self.a -= 1
        return env.b

    def test_circular_references(self):
        self.rc.new_expression(b=self.fn_circular)
        self.rc.run()
        assert self.rc['c'].exec_count is 4
        self.rc.set_value(a=3)
        assert self.rc['c'].exec_count is 8

    def test_simple_recursion(self):
        self.rc.new_expression(b=self.fn_recursive)
        self.rc.run()
        assert self.rc['c'].exec_count is 2
        assert self.rc['b'].exec_count is 4

    def test_nonreactive_recursion(self):
        self.a = 3
        self.rc.new_expression(b=self.fn_nonreactive)
        self.rc.run()
        assert self.rc['b'].exec_count is 4
        assert self.rc['c'].value is 0

    def test_circular_observer_only(self):
        self.rc.new_value(b=0)
        self.rc.new_observer(d=self.fn_circular)
        self.rc.run()
        assert self.rc['d'].exec_count is 4


def test_isolation_works():
    rc = Context()
    rc.new_value(x=1, y=10)
    rc.new_expression('b', lambda env: env.y + 100)
    rc.new_observer('c', lambda env: env.x + env[:].y + env[:].b)
    rc.new_observer('d', lambda env: env.x + env[:].y + env.b)

    rc.run()
    assert rc['c'].value is 121
    assert rc['c'].exec_count is 1
    assert rc['d'].value is 121
    assert rc['d'].exec_count is 1

    rc.set_value(x=2)
    assert rc['c'].value is 122
    assert rc['c'].exec_count is 2
    assert rc['d'].value is 122
    assert rc['d'].exec_count is 2

    rc.set_value(y=20)
    assert rc['c'].value is 122
    assert rc['c'].exec_count is 2
    assert rc['d'].value is 142
    assert rc['d'].exec_count is 3

    rc.set_value(x=3)
    assert rc['c'].value is 143
    assert rc['c'].exec_count is 3
    assert rc['d'].value is 143
    assert rc['d'].exec_count is 4


def test_block_isolation():
    def c1(env):
        with ~env:
            return env.a + 1

    def c2(env):
        with env[...] as e:
            return e.a + 1

    def c3(env):
        return env.a + 1

    rc = Context()
    rc.new_value(a=1)
    rc.new_observer(c1=c1, c2=c2, c3=c3)

    rc.run()
    assert rc['c1'].exec_count is 1
    assert rc['c1'].value is 2
    assert rc['c2'].exec_count is 1
    assert rc['c2'].value is 2
    assert rc['c3'].exec_count is 1
    assert rc['c3'].value is 2

    rc.set_value(a=2)
    assert rc['c1'].exec_count is 1
    assert rc['c1'].value is 2
    assert rc['c2'].exec_count is 1
    assert rc['c2'].value is 2
    assert rc['c3'].exec_count is 2
    assert rc['c3'].value is 3


def test_write_then_read():
    def b(env):
        env.a = env[:].a - 1
        return env.a

    rc = Context()
    rc.new_value(a=3)
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert rc['c'].exec_count is 1

    rc.set_value(a=10)
    assert rc['c'].exec_count is 2


def test_children_parents():
    rc = Context()
    rc.new_value(a=1)
    assert len(rc['a'].children) is 0
    rc.get_value('a')
    assert len(rc['a'].children) is 0

    rc.new_observer('b', lambda env: env.a)
    rc.run()
    assert len(rc['a'].children) is 1
    assert len(rc['a'].parents) is 0
    assert len(rc['b'].parents) is 1
    assert len(rc['b'].children) is 0


def test_observer_suspending():
    rc = Context()
    rc.new_value(v=1)
    rc.new_expression('a', lambda env: env.v)
    rc.new_observer('b', lambda env: env.a)

    raises(Exception, rc.suspend, 'v')
    raises(Exception, rc.suspend, 'a')
    raises(Exception, rc.resume, 'v')
    raises(Exception, rc.resume, 'a')
    rc.suspend('b')
    rc.run()
    assert rc['a'].exec_count is 1
    assert rc['b'].exec_count is 1

    rc.resume('b')
    rc.run()
    assert rc['a'].exec_count is 1
    assert rc['b'].exec_count is 1

    rc.suspend('b')
    assert not rc['b'].invalidated
    rc.set_value(v=2)
    assert rc['b'].invalidated
    assert rc['a'].exec_count is 1
    assert rc['b'].exec_count is 1

    rc['b'].resume()
    rc.set_value(v=2.5)
    rc['b'].suspend()
    rc.run()
    assert rc['a'].exec_count is 2
    assert rc['b'].exec_count is 2

    rc.set_value(v=3)
    assert rc['a'].exec_count is 2
    assert rc['b'].exec_count is 2

    assert rc['b'].invalidated
    rc.set_value(v=4)
    rc['b'].resume()
    rc.run()
    assert rc['a'].exec_count is 3
    assert rc['b'].exec_count is 3
    assert not rc['b'].invalidated

    rc.suspend('b')
    rc.set_value(v=5)
    rc.resume('b', run=True)
    assert rc['a'].exec_count is 4
    assert rc['b'].exec_count is 4


def test_safe_mode():
    def b1(env):
        if len(env.a) > 0:
            env.a.pop()
        return env.a

    rc = Context(safe=True)
    rc.new_value(a=[1, 2, 3])
    rc.new_expression(b=b1)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 4
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.safe = False
    rc.set_value(a=[1, 2, 3])
    assert rc['b'].exec_count is 5
    assert rc['c'].exec_count is 5
    assert len(rc['b'].value) is 2
    assert len(rc['c'].value) is 2

    def b2(env):
        env.b1.pop()
        return env.a

    rc = Context(safe=True)
    rc.new_value(a=[1, 2, 3])
    rc.new_expression(b1=lambda env: list(env.a))
    rc.new_expression(b2=b2)
    rc.new_observer('c', lambda env: (env.b1, env.b2))

    raises(Exception, rc.run)

    rc = Context(safe=False)
    rc.new_value(a=[1, 2, 3])
    rc.new_expression(b1=lambda env: list(env.a))
    rc.new_expression(b2=b2)
    rc.new_observer('c', lambda env: (env.b1, env.b2))
    rc.run()
    assert rc['b1'].exec_count is 1
    assert rc['b2'].exec_count is 1
    assert rc['c'].exec_count is 1

    def b3(env):
        if len(env.a1) > 0:
            return env.a1.pop()
        return 0

    rc = Context(safe=True)
    a = [1, 2, 3]
    rc.new_value(a1=a, a2=a)
    rc.new_expression(b=b3)
    rc.new_observer('c', lambda env: env.b)
    rc.run()
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 4
    assert rc['b'].value is 0
    assert rc['c'].value is 0
    assert len(rc['a1'].value) is 0
    assert len(rc['a2'].value) is 0
    assert len(a) is 0

    a.extend([1, 2])
    rc.run()
    assert rc['b'].exec_count is 7
    assert rc['c'].exec_count is 7
    assert rc['b'].value is 0
    assert rc['c'].value is 0
    assert len(rc['a1'].value) is 0
    assert len(rc['a2'].value) is 0
    assert len(a) is 0


def test_memoize_and_safe_mode():
    def b1(env):
        if len(env.a) > 0:
            env.a.pop()
        return env.a

    rc = Context(safe=True)
    rc.new_value(a=[1, 2, 3])
    rc.new_expression(b=b1)
    rc.memoize('b')
    rc.new_observer('c', lambda env: env.b)

    raises(Exception, rc.memoize, 'a')
    raises(Exception, rc.memoize, 'c')
    rc.memoize(rc['b'], False)
    assert not rc['b'].memoized
    rc.memoize('b', True)
    assert rc['b'].memoized

    rc.run()
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 4
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.set_value(a=[1, 2, 3])
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 5
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.set_value(a=[1, 2])
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 6
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.safe = False

    rc.set_value(a=[1, 2, 3])
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 7
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.set_value(a=[1])
    assert rc['b'].exec_count is 4
    assert rc['c'].exec_count is 8
    assert len(rc['b'].value) is 0
    assert len(rc['c'].value) is 0

    rc.set_value(a=[10, 20])
    assert rc['b'].exec_count is 5
    assert rc['c'].exec_count is 9
    assert len(rc['b'].value) is 1
    assert len(rc['c'].value) is 1


def test_external_access():
    rc = Context()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 1)
    rc.new_observer('c', lambda env: env.b + 1)

    b = rc['b'].get_value()
    assert b is 2
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 0

    rc.run()
    assert rc['c'].value is 3
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 1

    rc = Context()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 1)
    rc.new_observer('c', lambda env: env.b + 1)

    b = rc['b'].get_value()
    assert b is 2
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 0

    rc.set_value(a=2)
    assert rc['b'].exec_count is 1
    assert rc['c'].exec_count is 0

    raises(Exception, rc.get_value, 'c')


class TestLog(object):
    def setup(self):
        self.buf = StringIO()
        self.rc = Context(log=self.buf)

    @property
    def text(self):
        return self.buf.getvalue()

    def test_stream(self):
        assert self.rc._log_stream is self.buf
        self.rc.stop_log()
        assert self.rc._log_stream is None
        self.rc.start_log()
        assert self.rc._log_stream is sys.stdout
        self.rc = Context(log=True)
        assert self.rc._log_stream is sys.stdout

    def test_formatter_1(self):
        self.rc.log('%s %s', self.rc._fmt_value([1, 2]), self.rc._fmt_value({1: 2}))
        assert self.text == '[1, 2] {1: 2}\n'

    def test_formatter_2(self):
        self.rc.start_log(self.buf, lambda x: 'x' if isinstance(x, dict) else x)
        self.rc.log('%s %s', self.rc._fmt_value([1, 2]), self.rc._fmt_value({1: 2}))
        assert self.text == '[1, 2] x\n'

    def test_log_1(self):
        self.rc.log('a %r %d', [1], 2)
        assert self.text == 'a [1] 2\n'

    def test_log_2(self):
        with self.rc.log_block('b'):
            self.rc.log('c')
        assert self.text == 'b\n  c\n'

    def test_log_3(self):
        with self.rc.log_block():
            self.rc.log('c')
        assert self.text == '  c\n'

    def test_log_4(self):
        try:
            self.rc.log('a')
            with self.rc.log_block('b'):
                self.rc.log('c')
                raise Exception
        except:
            pass
        self.rc.log('d')
        assert self.text == 'a\nb\n  c\nd\n'

    def test_log_5(self):
        self.rc.stop_log()
        self.rc.log('a')
        with self.rc.log_block('b'):
            self.rc.log('c')
        assert self.text == ''
