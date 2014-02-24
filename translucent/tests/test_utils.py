# -*- coding: utf-8

from translucent import patch_thread
patch_thread()

from translucent.utils import (is_string, is_number, is_valid_name, is_options_expression,
    new_closure, to_json)

from pytest import raises


def test_is_string():
    assert is_string('test')
    assert is_string(u'test')
    assert not is_string(1)
    assert not is_string([1])
    assert not is_string({1: 1})


def test_is_number():
    assert is_number(1)
    assert is_number(1L)
    assert is_number(1.)
    assert not is_number('test')
    assert not is_number([1])
    assert not is_number({1: 1})


def test_is_valid_name():
    assert is_valid_name('test')
    assert is_valid_name('_test123')
    assert is_valid_name('Test')
    assert not is_valid_name(' test')
    assert not is_valid_name('$test')
    assert not is_valid_name('123test')
    assert not is_valid_name(1)


def test_is_option_expression():
    valid_expressions = [
        'label for value in array',
        'select as label for value in array',
        'label group by group for value in array',
        'select as label group by group for value in array track by trackexpr',
        'label for (key , value) in object',
        'select as label for (key , value) in object',
        'label group by group for (key, value) in object',
        'select as label group by group for (key, value) in object'
    ]
    for expression in valid_expressions:
        assert is_options_expression(expression)
    assert not is_options_expression('a for b')
    assert not is_options_expression('')
    assert not is_options_expression(1)


def test_new_closure():
    y = [100]
    f1 = new_closure('f1', ['x'], 'return x + y[0] + 1', closure={'y': y}, docstring='test')
    assert f1.__doc__ == 'test'
    assert f1(1) is 102
    assert f1(x=1) is 102
    raises(TypeError, f1)
    raises(TypeError, f1, 1, 2)
    raises(TypeError, f1, 1, y=1)
    raises(Exception, new_closure, '$f', [], 'pass')
    raises(Exception, new_closure, 'f', [], 'pass', kwargs='$f')
    raises(Exception, new_closure, 'f', ['x'], 'pass', defaults={'y': 1})
    raises(Exception, new_closure, 'f', ['x'], 'pass', defaults={'x': object()})
    raises(Exception, new_closure, 'f', ['x', 'y'], 'pass', defaults={'x': 1})
    raises(IndentationError, new_closure, 'f', [], '')
    f2 = new_closure('f2', [], 'pass', docstring=None)
    assert f2.__doc__ is None


def test_to_json():
    raises(Exception, to_json, object())
    assert to_json(1) == '1'
    assert to_json('1') == "'1'"
    assert to_json(None) == 'null'
    assert to_json("'1'") == "'\\'1\\''"
    assert to_json(True) == 'true'
    assert to_json(False) == 'false'
    assert to_json((1, 2, '3')) == "[1,2,'3']"
    raises(Exception, to_json, {1: 2})
    assert to_json({'1': 2, '3': '4'}) in ["{'1':2,'3':'4'}", "{'3':'4','1':2}"]
    assert to_json([1, '2', {'3': [4, {'5': 6}]}]) == "[1,'2',{'3':[4,{'5':6}]}]"
    assert to_json('1', single=False) == '"1"'
    assert to_json('"1"', single=False) == '"\\"1\\""'
    assert to_json({'1': [2, 3]}, sep=(', ', ': ')) == "{'1': [2, 3]}"
