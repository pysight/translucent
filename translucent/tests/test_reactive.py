# -*- coding: utf-8

import sys
from cStringIO import StringIO
from nose.tools import assert_true, assert_false, assert_equals, assert_raises
from translucent.reactive import (UndefinedKey,
    ReactiveContext, ReactiveValue, ReactiveExpression, ReactiveObserver)


def test_object_name():

    assert_raises(Exception, ReactiveValue, '_', None)
    assert_raises(Exception, ReactiveValue, '123name', 1)
    assert_raises(Exception, ReactiveValue, '_name123', None)
    assert_raises(Exception, ReactiveValue, '$1', None)
    assert_equals(ReactiveValue('__name', 1).name, '__name')
    assert_equals(ReactiveValue('__1', None).name, '__1')


def test_object_type():

    v = ReactiveValue('v', None)
    e = ReactiveExpression('e', id)
    o = ReactiveObserver('o', id)

    assert_false(v.is_observer())
    assert_false(e.is_observer())
    assert_true(o.is_observer())

    assert_true(v.is_value())
    assert_false(e.is_value())
    assert_false(o.is_value())

    assert_false(v.is_expression())
    assert_true(e.is_expression())
    assert_false(o.is_expression())


def test_constructors():

    rc = ReactiveContext

    assert_equals(rc().new_value(a=1, b=2), None)
    assert_equals(rc().new_value('a', 1, 'b', 2), None)
    assert_equals(rc().new_value('a', 1, b=2), None)
    assert_equals(rc().new_value('a', 1, b=2), None)
    assert_raises(Exception, lambda: rc().new_value('a', 1, b=2)['b'])

    assert_raises(Exception, rc().new_value)
    assert_raises(Exception, rc().new_value, 'a')
    assert_raises(Exception, rc().new_value, 'a', 1, 'b', c=2)
    assert_raises(Exception, rc().new_value, 'a', 1, a=2)

    assert_equals(rc().new_value('a', 1).name, 'a')
    assert_equals(rc().new_value(a=1).name, 'a')
    assert_equals(rc().new_value(a=1).name, 'a')
    assert_equals(rc().new_value(a=1).name, 'a')
    assert_true(rc().new_value(a=1).is_value())


def test_decorators():

    rc = ReactiveContext()
    rc.new_value(a=1)

    @rc.expression('b')
    def b(env):
        return env.a + 1

    @rc.observer('c')
    def c(env):
        return env.b + 1

    rc.run()
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)
    assert_equals(rc['c'].value, 3)

    assert_raises(Exception, rc.expression, 'hello', 'world')
    assert_raises(Exception, rc.expression('hello'), 'world')

    assert_raises(Exception, rc.observer, 'hello', 'world')
    assert_raises(Exception, rc.observer('hello'), 'world')


def test_undefined_key():

    try:
        raise UndefinedKey('a')
    except UndefinedKey as e:
        assert_equals(e.name, 'a')

    rc = ReactiveContext()
    rc.new_expression('b', lambda env: env.a + 1)
    rc.new_observer('c', lambda env: env.b + 1)
    assert_raises(Exception, lambda: rc['a'])

    rc.run()
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)

    rc.new_value(a=1)
    assert_equals(rc['b'].exec_count, 2)
    assert_equals(rc['c'].exec_count, 2)
    assert_equals(rc['c'].value, 3)


def test_environment():

    rc = ReactiveContext()
    assert_equals(rc.env._context, rc)
    assert_equals(rc.env._isolate, False)
    assert_raises(UndefinedKey, lambda: rc.env.a)
    assert_raises(UndefinedKey, lambda: rc.env['a'])
    env = rc.env[:]
    assert_equals(env._context, rc)
    assert_equals(env._isolate, True)


def test_set_same_value():

    rc = ReactiveContext()
    rc.new_value(a=1)
    rc.new_observer('b', lambda env: env.a)

    rc.run()
    assert_equals(rc['b'].exec_count, 1)

    rc.set_value(a=1)
    assert_equals(rc['b'].exec_count, 1)


def test_overreactivity_1():

    rc = ReactiveContext()
    rc.new_value(v=1)
    rc.new_expression('a', lambda env: env.v)
    rc.new_expression('b', lambda env: env.a + env.v)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)

    rc.set_value(v=11)
    assert_equals(rc['b'].exec_count, 2)
    assert_equals(rc['c'].exec_count, 2)


def test_overreactivity_2():

    rc = ReactiveContext()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.b * env.a)
    rc.new_observer('d', lambda env: env.b * env.a)

    rc.run()
    assert_equals(rc['c'].value, 6)
    assert_equals(rc['d'].value, 6)
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)
    assert_equals(rc['d'].exec_count, 1)

    rc.set_value(a=2)
    assert_equals(rc['c'].value, 14)
    assert_equals(rc['d'].value, 14)
    assert_equals(rc['b'].exec_count, 2)
    assert_equals(rc['c'].exec_count, 2)
    assert_equals(rc['d'].exec_count, 2)


def test_order_of_evaluation():

    rc = ReactiveContext()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.a * env.b)

    rc.run()
    assert_equals(rc['c'].value, 6)
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)

    rc.set_value(a=2)
    assert_equals(rc['c'].value, 14)
    assert_equals(rc['b'].exec_count, 2)
    assert_equals(rc['c'].exec_count, 2)

    rc = ReactiveContext()
    rc.new_value(a=1)
    rc.new_expression('b', lambda env: env.a + 5)
    rc.new_observer('c', lambda env: env.b * env.a)

    rc.run()
    assert_equals(rc['c'].value, 6)
    assert_equals(rc['b'].exec_count, 1)
    assert_equals(rc['c'].exec_count, 1)

    rc.set_value(a=2)
    assert_equals(rc['c'].value, 14)
    assert_equals(rc['b'].exec_count, 2)
    assert_equals(rc['c'].exec_count, 2)


def test_circular_references():

    def b(env):
        if env['a'] is 0:
            return 0
        env['a'] -= 1
        return env['a']

    rc = ReactiveContext()
    rc.new_value('a', 3)
    rc.new_expression('b', b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['c'].exec_count, 4)

    rc.set_value('a', 3)
    assert_equals(rc['c'].exec_count, 8)


def test_simple_recursion():

    def b(env):
        if env.a is 0:
            return 0
        env.a -= 1
        return env.b

    rc = ReactiveContext()
    rc.new_value(a=5)
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['c'].exec_count, 2)
    assert_equals(rc['b'].exec_count, 6)


def test_nonreactive_recursion():

    a = [3]

    def b(env):
        if a[0] is 0:
            return 0
        a[0] -= 1
        return env.b

    rc = ReactiveContext()
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['b'].exec_count, 4)
    assert_equals(rc['c'].value, 0)


def test_circular_observer_only():

    def b(env):
        if env.a is 0:
            return 0
        env.a -= 1

    rc = ReactiveContext()
    rc.new_value(a=3)
    rc.new_observer(b=b)

    rc.run()
    assert_equals(rc['b'].exec_count, 4)


def test_isolation_works():

    rc = ReactiveContext()
    rc.new_value(x=1, y=10)
    rc.new_expression('b', lambda env: env.y + 100)
    rc.new_observer('c', lambda env: env.x + env[:].y + env[:].b)
    rc.new_observer('d', lambda env: env.x + env[:].y + env.b)

    rc.run()
    assert_equals(rc['c'].value, 121)
    assert_equals(rc['c'].exec_count, 1)
    assert_equals(rc['d'].value, 121)
    assert_equals(rc['d'].exec_count, 1)

    rc.set_value(x=2)
    assert_equals(rc['c'].value, 122)
    assert_equals(rc['c'].exec_count, 2)
    assert_equals(rc['d'].value, 122)
    assert_equals(rc['d'].exec_count, 2)

    rc.set_value(y=20)
    assert_equals(rc['c'].value, 122)
    assert_equals(rc['c'].exec_count, 2)
    assert_equals(rc['d'].value, 142)
    assert_equals(rc['d'].exec_count, 3)

    rc.set_value(x=3)
    assert_equals(rc['c'].value, 143)
    assert_equals(rc['c'].exec_count, 3)
    assert_equals(rc['d'].value, 143)
    assert_equals(rc['d'].exec_count, 4)


def test_block_isolation():

    def c1(env):
        with ~env:
            return env.a + 1

    def c2(env):
        with env[...] as e:
            return e.a + 1

    def c3(env):
        return env.a + 1

    rc = ReactiveContext()
    rc.new_value(a=1)
    rc.new_observer(c1=c1, c2=c2, c3=c3)

    rc.run()
    assert_equals(rc['c1'].exec_count, 1)
    assert_equals(rc['c1'].value, 2)
    assert_equals(rc['c2'].exec_count, 1)
    assert_equals(rc['c2'].value, 2)
    assert_equals(rc['c3'].exec_count, 1)
    assert_equals(rc['c3'].value, 2)

    rc.set_value(a=2)
    assert_equals(rc['c1'].exec_count, 1)
    assert_equals(rc['c1'].value, 2)
    assert_equals(rc['c2'].exec_count, 1)
    assert_equals(rc['c2'].value, 2)
    assert_equals(rc['c3'].exec_count, 2)
    assert_equals(rc['c3'].value, 3)


def test_write_then_read():

    def b(env):
        env.a = env[:].a - 1
        return env.a

    rc = ReactiveContext()
    rc.new_value(a=3)
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['c'].exec_count, 1)

    rc.set_value(a=10)
    assert_equals(rc['c'].exec_count, 2)


def test_children_parents():

    rc = ReactiveContext()
    rc.new_value(a=1)
    assert_equals(len(rc['a'].children), 0)
    rc.get_value('a')
    assert_equals(len(rc['a'].children), 0)

    rc.new_observer('b', lambda env: env.a)
    rc.run()
    assert_equals(len(rc['a'].children), 1)
    assert_equals(len(rc['a'].parents), 0)
    assert_equals(len(rc['b'].parents), 1)
    assert_equals(len(rc['b'].children), 0)


def test_observer_suspending():

    rc = ReactiveContext()
    rc.new_value(v=1)
    rc.new_expression('a', lambda env: env.v)
    rc.new_observer('b', lambda env: env.a)

    assert_raises(Exception, rc.suspend, 'v')
    assert_raises(Exception, rc.suspend, 'a')
    rc.suspend('b')
    rc.run()
    assert_equals(rc['a'].exec_count, 1)
    assert_equals(rc['b'].exec_count, 1)

    rc.resume('b')
    rc.run()
    assert_equals(rc['a'].exec_count, 1)
    assert_equals(rc['b'].exec_count, 1)

    rc.suspend('b')
    assert_false(rc['b'].invalidated)
    rc.set_value(v=2)
    assert_true(rc['b'].invalidated)
    assert_equals(rc['a'].exec_count, 1)
    assert_equals(rc['b'].exec_count, 1)

    rc['b'].resume()
    rc.set_value(v=2.5)
    rc['b'].suspend()
    rc.run()
    assert_equals(rc['a'].exec_count, 2)
    assert_equals(rc['b'].exec_count, 2)

    rc.set_value(v=3)
    assert_equals(rc['a'].exec_count, 2)
    assert_equals(rc['b'].exec_count, 2)

    assert_true(rc['b'].invalidated)
    rc.set_value(v=4)
    rc['b'].resume()
    rc.run()
    assert_equals(rc['a'].exec_count, 3)
    assert_equals(rc['b'].exec_count, 3)
    assert_false(rc['b'].invalidated)

    rc.suspend('b')
    rc.set_value(v=5)
    rc.resume('b', run=True)
    assert_equals(rc['a'].exec_count, 4)
    assert_equals(rc['b'].exec_count, 4)


def test_safe_mode():

    def b(env):
        if len(env.a) > 0:
            env.a.pop()

    rc = ReactiveContext(safe=True)
    rc.new_value(a=[1, 2, 3])
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['b'].exec_count, 4)
    assert_equals(rc['c'].exec_count, 4)


def test_log():

    buf = StringIO()

    rc = ReactiveContext(log=buf)
    assert_equals(rc.log_stream, buf)

    rc.stop_log()
    assert_equals(rc.log_stream, None)

    rc.start_log()
    assert_equals(rc.log_stream, sys.stdout)

    rc.start_log(buf)
    rc.log('a %r %d', [1], 2)
    assert_equals(buf.getvalue(), 'a [1] 2\n')

    buf.truncate(0)
    with rc.log_block('b'):
        rc.log('c')
    assert_equals(buf.getvalue(), 'b\n  c\n')

    buf.truncate(0)
    with rc.log_block():
        rc.log('c')
    assert_equals(buf.getvalue(), '  c\n')

    buf.truncate(0)
    try:
        rc.log('a')
        with rc.log_block('b'):
            rc.log('c')
            raise Exception
    except:
        pass
    rc.log('d')
    assert_equals(buf.getvalue(), 'a\nb\n  c\nd\n')

    buf.truncate(0)
    rc.log('%s %s', rc.fmt_value([1, 2]), rc.fmt_value({1: 2}))
    assert_equals(buf.getvalue(), '[1, 2] {1: 2}\n')

    buf.truncate(0)
    formatter = lambda x: 'x' if isinstance(x, dict) else x
    rc.start_log(buf, formatter)
    rc.log('%s %s', rc.fmt_value([1, 2]), rc.fmt_value({1: 2}))
    assert_equals(buf.getvalue(), '[1, 2] x\n')

    buf.truncate(0)
    rc.stop_log()
    rc.log('a')
    with rc.log_block('b'):
        rc.log('c')
    assert_equals(buf.getvalue(), '')
