# -*- coding: utf-8

from nose.tools import assert_true, assert_false, assert_equals, assert_raises
from translucent.reactive import (
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


def test_order_of_evaluation_1():

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
        if env.a is 0:
            return 0
        env.a -= 1
        return env.a

    rc = ReactiveContext()
    rc.new_value(a=3)
    rc.new_expression(b=b)
    rc.new_observer('c', lambda env: env.b)

    rc.run()
    assert_equals(rc['c'].exec_count, 4)

    rc.set_value(a=3)
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


def test_isolate_no_dependency_propagation():

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


def test_write_then_read_not_circular():

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
