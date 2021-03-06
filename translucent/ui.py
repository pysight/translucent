# -*- coding: utf-8 -*-

import jinja2
import yaml
from collections import Hashable, Callable

from .utils import (
    new_closure, is_valid_name, is_options_expression, is_string, to_json, is_number)
from .html import format_page, escape, attr_if, class_fmt
from ._compat import OrderedDict


class Component(object):

    def __init__(self, fn, docstring=None):
        self.fn = fn
        if docstring:
            self.__doc__ = docstring

    def __getitem__(self, key):
        return self.fn(*key) if isinstance(key, tuple) else self.fn(key)

    def __call__(self, *args):
        return self.fn(*args)


class ComponentWrapper(object):

    def __init__(self, fn):
        self.fn = fn
        self.__call__ = fn

    def __getitem__(self, key):
        return self()[key]

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


def merge(*contents):
    if not contents:
        return ''
    rendered_contents = []
    for element in contents:
        if isinstance(element, jinja2.Markup):
            s = str(element)
        elif isinstance(element, list):
            s = merge(*element)
        elif is_string(element):
            s = escape(element)
        elif isinstance(element, Component):
            s = str(element())
        elif isinstance(element, ComponentWrapper):
            s = str(element()())
        else:
            raise Exception('cannot render element: %s' % repr(element))
        rendered_contents.append(str(s).strip())
    return jinja2.Markup(' '.join(rendered_contents))


@jinja2.contextfunction
def debug(context, *args):
    print ' '.join(map(str, args))


class RenderEngine(object):

    def __init__(self, layout=None, title=''):
        try:
            rel_path = '../templates'
            self.loader = jinja2.PackageLoader(__package__, rel_path)
        except:
            self.loader = jinja2.FileSystemLoader(rel_path)
        self.layout = layout
        self.title = title
        self.components = {}
        self.macros = {}
        self.blocks = {}
        self.value_types = {}
        self.env = jinja2.Environment(loader=self.loader)
        self.root_template = self.env.get_template('index.html')
        self.register_components('components/default.yml')
        self.register_filter('to_json', to_json)
        self.register_function('attr_if', attr_if)
        self.register_function('class_fmt', class_fmt)
        self.register_function('debug', debug)
        self.register_macros('macros', self.load_source('macros.html'))
        self.register_default_value_types()
        self.outputs = {}

    def load_source(self, path):
        return self.loader.get_source(self.env, path)[0]

    def register_filter(self, name, fn):
        self.env.filters[name] = fn

    def register_components(self, components):
        if is_string(components):
            components = yaml.load(self.load_source(components))
        for name, component in components.iteritems():
            if not is_valid_name(name) or name[0] == '_':
                raise Exception('invalid component name: "%s"' % name)
            if 'template' not in component:
                raise Exception('template missing for component "%s"' % name)
            args = component.get('args', {}) or {}
            if isinstance(args, list):
                args = OrderedDict(item for arg in map(dict.items, args) for item in arg)
            component['args'] = args
        self.components.update(components)
        self.generate_components(components)

    def register_macros(self, name, macros):
        self.macros[name] = self.env.from_string(macros)

    def register_function(self, name, fn):
        self.env.globals[name] = fn

    def register_value_type(self, name, value_type, docstring=None):
        if not is_string(name) or name[0] != '$' or not is_valid_name(name[1:]):
            raise Exception('invalid name for value type name: "%s"' % name)
        if type(value_type) is type:
            fn = lambda v: isinstance(v, value_type)
        elif isinstance(value_type, list):
            fn = lambda v: v in value_type
        elif isinstance(value_type, Callable):
            fn = value_type
        elif isinstance(value_type, Hashable):
            fn = lambda v: v == value_type
        else:
            raise Exception('value type must be a type, a list, a callable, or a hashable')
        self.value_types[name] = {'fn': fn, 'docstring': docstring}

    def register_default_value_types(self):
        is_text_type = lambda v: isinstance(v, (list, basestring))
        self.register_value_type('$bool', bool, 'bool')
        self.register_value_type('$none', None, 'None')
        self.register_value_type('$text', is_text_type, 'text')
        self.register_value_type('$string', is_string, 'string')
        self.register_value_type('$number', is_number, 'number')
        self.register_value_type('$list', list, 'list')
        self.register_value_type('$dict', dict, 'dict')
        self.register_value_type('$options', is_options_expression, 'options')
        self.register_value_type('$id', is_valid_name, 'id')

    def generate_imports(self):
        return ''.join(['{%% import %(macros)s as %(macros)s with context %%}\n' %
            {'macros': key} for key in self.macros.keys()])

    def generate_components(self, components=None):
        components = components or self.components
        for name, component in components.iteritems():
            args = component['args']
            fn_args = ', '.join([arg + '=' + arg for arg in args.iterkeys()] + ['**kwargs'])
            code = "return self.render_component('%s', %s)" % (name, fn_args)
            docstring = component.get('docstring', None)
            defaults = dict((k, v['default']) for k, v in args.iteritems() if 'default' in v)
            wrapper = ComponentWrapper(new_closure(name, args.keys(), code, defaults=defaults,
                docstring=docstring, kwargs='kwargs', closure={'self': self}))
            setattr(self, name, wrapper)

    def render_component(self, _component_name, **kwargs):
        if _component_name not in self.components:
            raise Exception('unknown component: "%s"' % _component_name)
        component = self.components[_component_name]
        nav = kwargs.pop('nav', None)
        args = self.parse_args(component, kwargs)
        template = self.env.from_string(self.generate_imports() + component['template'])
        args.update(self.macros)
        if component.get('output', False):
            self.outputs[kwargs['id']] = _component_name

        def render_fn(*contents):
            if contents and not component.get('container', False):
                raise Exception('component "%s" is not a container' % _component_name)
            args['contents'] = self.merge(*contents)
            args['raw_contents'] = map(lambda c: self.merge(c), contents)
            html = jinja2.Markup(template.render(**args))
            return html if not nav else self.nav(text=nav)(html)
        return Component(render_fn)

    def render_layout(self):
        html = self.root_template.render(layout=self.layout, title=self.title, **self.blocks)
        return format_page(html)

    def set(self, name):
        def block_fn(*contents):
            self.blocks[name] = jinja2.Markup(self.merge(*contents))
        return block_fn

    def validate_value(self, option, value):
        if option[0] is not '$':
            return option == value
        elif option in self.value_types:
            return self.value_types[option]['fn'](value)
        return False

    def parse_args(self, component, kwargs):
        expr = dict((arg, False) for arg in kwargs.keys())
        for arg, value in kwargs.iteritems():
            if arg not in component['args']:
                raise Exception('unknown argument: "%s"' % arg)
            options = map(str.strip, component['args'][arg]['values'].split('|'))
            expression_allowed = '$expression' in options
            options = filter(lambda option: option != '$expression', options)
            match_found = any(map(lambda o: self.validate_value(o, value), options))
            if not match_found:
                if not expression_allowed:
                    raise Exception('invalid argument: %s=%s' % (arg, repr(value)))
                if not is_string(value):
                    raise Exception('%s: expected expresssion, got %s' % (arg, repr(value)))
                expr[arg] = True
            elif '$text' in options and isinstance(value, list):
                if '$list' not in options or options.index('$list') > options.index('$text'):
                    kwargs[arg] = self.merge(*kwargs[arg])
        return {'args': kwargs.copy(), 'expr': expr}

    @staticmethod
    def merge(*contents):
        return merge(*contents)
