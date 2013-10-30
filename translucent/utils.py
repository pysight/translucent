# -*- coding: utf-8 -*-

import textwrap
import jinja2
import types
import re


def tojson(obj, single=True, sep=(',', ':')):
    c = "'" if single else '"'
    quote = lambda s: c + s.replace(c, '\\' + c) + c
    if obj is None:
        return 'null'
    elif obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif isinstance(obj, basestring):
        return quote(obj)
    elif isinstance(obj, (int, long, float)):
        return str(obj)
    elif isinstance(obj, (tuple, list)):
        return '[%s]' % sep[0].join([tojson(elem) for elem in obj])
    elif isinstance(obj, dict):
        return '{%s}' % sep[0].join(['%s%s%s' %
            (quote(k), sep[1], tojson(v)) for k, v in obj.iteritems()])
    raise Exception('cannot convert to json: "%s"' % str(obj))


def escape_text(text, angular=True):
    escape = lambda s: str(jinja2.escape(s))
    if not angular:
        return escape(text)
    else:
        index, parts = 0, []
        while index < len(text):
            start = text.find('{{', index)
            end = text.find('}}', start + 2)
            if start is not -1 and end is not -1:
                if start is not index:
                    parts.append(escape(text[index:start]))
                parts.append(text[start:end + 2])
                index = end + 2
            else:
                parts.append(escape(text[index:]))
                break
        return ''.join(parts)


def new_closure(name, args, code, defaults=None, closure=None, kwargs=None, docstring=None):
    defaults = defaults or {}
    for arg in defaults.iterkeys():
        if arg not in args:
            raise Exception('invalid default: non-existent argument "%s"' % arg)
    defaults_locations = tuple(sorted(map(args.index, defaults.keys())))
    expected_locations = tuple(range(len(args) - len(defaults), len(args)))
    if defaults_locations != expected_locations:
        raise Exception('default values not allowed before positional arguments')
    args = ', '.join([arg if arg not in defaults else '%s=%s' % (arg,
        repr(defaults[arg])) for arg in args] + ['**' + kwargs] if kwargs else [])
    closure = closure or {}
    code = '\n'.join(['\t\t' + line for line in textwrap.dedent(code).split('\n')])
    code = 'def _({closure}):\n\tdef {name}({args}):\n{code}\n\treturn {name}'.replace(
        '\t', ' ' * 4).format(name=name, closure=', '.join(closure.keys()), args=args, code=code)
    types.FunctionType(compile(code, __name__, 'exec'), globals(), name)()
    fn = globals()['_'](*closure.values())
    if docstring is not None:
        fn.__doc__ = docstring
    return fn


def is_valid_name(name):
    return re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', name)
