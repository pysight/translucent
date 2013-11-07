# -*- coding: utf-8 -*-

import textwrap
import types
import re


def is_string(x):
    return isinstance(x, basestring)


def is_number(x):
    return isinstance(x, (int, long, float))


def is_valid_name(name):
    return is_string(name) and bool(re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', name))


def is_options_expression(s):
    return is_string(s) and bool(re.match(
        r'^\s*(.*?)(?:\s+as\s+(.*?))?(?:\s+group\s+by\s+(.*))?\s+' +
        r'for\s+(?:([\$\w][\$\w]*)|(?:\(\s*([\$\w][\$\w]*)\s*,\s*([\$\w][\$\w]*)\s*\)))\s+' +
        r'in\s+(.*?)(?:\s+track\s+by\s+(.*?))?$', s))


def to_json(obj, single=True, sep=(',', ':')):
    c = "'" if single else '"'
    quote = lambda s: c + s.replace(c, '\\' + c) + c
    if obj is None:
        return 'null'
    elif obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif is_string(obj):
        return quote(obj)
    elif is_number(obj):
        return str(obj)
    elif isinstance(obj, (tuple, list)):
        return '[%s]' % sep[0].join([to_json(elem, single, sep) for elem in obj])
    elif isinstance(obj, dict):
        if bool(any(not is_string(key) for key in obj.iterkeys())):
            raise Exception('non-string key in "%s"' % str(obj))
        return '{%s}' % sep[0].join(['%s%s%s' %
            (quote(k), sep[1], to_json(v, single, sep)) for k, v in obj.iteritems()])
    raise Exception('cannot convert to json: "%s"' % str(obj))


def new_closure(name, args, code, defaults=None, closure=None, kwargs=None, docstring=None):
    if not is_valid_name(name):
        raise Exception('invalid function name: "%s"' % name)
    if kwargs is not None and not is_valid_name(kwargs):
        raise Exception('invalid kwargs variable name: "%s"' % kwargs)
    defaults = defaults or {}
    for arg, v in defaults.iteritems():
        if arg not in args:
            raise Exception('invalid default key: non-existent argument "%s"' % arg)
        if not isinstance(v, (int, long, float, dict, basestring, list, tuple, type(None))):
            raise Exception('cannot serialize default value for "%s": "%s"' % (arg, v))
    defaults_locations = tuple(sorted(map(args.index, defaults.keys())))
    expected_locations = tuple(range(len(args) - len(defaults), len(args)))
    if defaults_locations != expected_locations:
        raise Exception('default values not allowed before positional arguments')
    args = ', '.join([arg if arg not in defaults else '%s=%s' % (arg,
        repr(defaults[arg])) for arg in args] + (['**' + kwargs] if kwargs else []))
    closure = closure or {}
    code = '\n'.join(['\t\t' + line for line in textwrap.dedent(code).split('\n')])
    code = 'def _({closure}):\n\tdef {name}({args}):\n{code}\n\treturn {name}'.format(
        name=name, closure=', '.join(closure.keys()), args=args, code=code).replace(
        '\t', ' ' * 4)
    types.FunctionType(compile(code, __name__, 'exec'), globals(), name)()
    fn = globals()['_'](*closure.values())
    if docstring is not None:
        fn.__doc__ = docstring
    return fn
