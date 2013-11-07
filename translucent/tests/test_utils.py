from nose.tools import assert_true, assert_false, assert_equals, assert_raises
from translucent.utils import (
    is_string, is_number, is_valid_name, is_options_expression, new_closure, to_json
)


def test_is_string():
    assert_true(is_string('test'))
    assert_true(is_string(u'test'))
    assert_false(is_string(1))
    assert_false(is_string([1]))
    assert_false(is_string({1: 1}))


def test_is_number():
    assert_true(is_number(1))
    assert_true(is_number(1L))
    assert_true(is_number(1.))
    assert_false(is_number('test'))
    assert_false(is_number([1]))
    assert_false(is_number({1: 1}))


def test_is_valid_name():
    assert_true(is_valid_name('test'))
    assert_true(is_valid_name('_test123'))
    assert_true(is_valid_name('Test'))
    assert_false(is_valid_name(' test'))
    assert_false(is_valid_name('$test'))
    assert_false(is_valid_name('123test'))
    assert_false(is_valid_name(1))


def test_is_option_expression():
    valid_expressions = [
        'label for value in array'
        'select as label for value in array'
        'label group by group for value in array'
        'select as label group by group for value in array track by trackexpr'
        'label for (key , value) in object'
        'select as label for (key , value) in object'
        'label group by group for (key, value) in object'
        'select as label group by group for (key, value) in object'
    ]
    for expression in valid_expressions:
        assert_true(is_options_expression(expression))
    assert_false(is_options_expression('a for b'))
    assert_false(is_options_expression(''))
    assert_false(is_options_expression(1))


def test_new_closure():
    y = [100]
    f1 = new_closure('f1', ['x'], 'return x + y[0] + 1', closure={'y': y}, docstring='test')
    assert_equals(f1.__doc__, 'test')
    assert_equals(f1(1), 102)
    assert_equals(f1(x=1), 102)
    assert_raises(TypeError, f1)
    assert_raises(TypeError, f1, 1, 2)
    assert_raises(TypeError, f1, 1, y=1)
    assert_raises(Exception, new_closure, '$f', [], 'pass')
    assert_raises(Exception, new_closure, 'f', [], 'pass', kwargs='$f')
    assert_raises(Exception, new_closure, 'f', ['x'], 'pass', defaults={'y': 1})
    assert_raises(Exception, new_closure, 'f', ['x'], 'pass', defaults={'x': object()})
    assert_raises(Exception, new_closure, 'f', ['x', 'y'], 'pass', defaults={'x': 1})
    assert_raises(IndentationError, new_closure, 'f', [], '')
    f2 = new_closure('f2', [], 'pass', docstring=None)
    assert_equals(f2.__doc__, None)


def test_to_json():
    assert_raises(Exception, to_json, object())
    assert_equals(to_json(1), '1')
    assert_equals(to_json('1'), "'1'")
    assert_equals(to_json(None), 'null')
    assert_equals(to_json("'1'"), "'\\'1\\''")
    assert_equals(to_json(True), 'true')
    assert_equals(to_json(False), 'false')
    assert_equals(to_json((1, 2, '3')), "[1,2,'3']")
    assert_raises(Exception, to_json, {1: 2})
    assert_equals(to_json({'1': 2, '3': '4'}), "{'1':2,'3':'4'}")
    assert_equals(to_json([1, '2', {'3': [4, {'5': 6}]}]), "[1,'2',{'3':[4,{'5':6}]}]")
    assert_equals(to_json('1', single=False), '"1"')
    assert_equals(to_json('"1"', single=False), '"\\"1\\""')
    assert_equals(to_json({'1': [2, 3]}, sep=(', ', ': ')), "{'1': [2, 3]}")
