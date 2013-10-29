# -*- coding: utf-8 -*-

import jinja2
import yaml
import inspect
import bs4
import types
from collections import OrderedDict

from .utils import tojson, escape_text, new_closure


class Component:

    def __init__(self, fn, docstring=None):
        self.fn = fn
        if docstring:
            self.__doc__ = docstring

    def __getitem__(self, key):
        return self.fn(*key) if isinstance(key, tuple) else self.fn(key)

    def __call__(self, *args):
        return self.fn(*args)


class ComponentWrapper:

    def __init__(self, fn):
        self.__call__ = fn

    def __getitem__(self, key):
        return self()[key]


class BootstrapUI:

    def __init__(self, layout=None, title=''):
        try:
            loader = jinja2.PackageLoader(__package__, '../templates')
        except:
            loader = jinja2.FileSystemLoader('../templates')
        self.env = jinja2.Environment(loader=loader)
        get_source = lambda name: loader.get_source(self.env, name)[0]
        self.root_template = self.env.get_template('index.html')
        self.components = {}
        self.register_components(yaml.load(get_source('components.yml')))
        self.register_filter('tojson', tojson)
        self.macros = {}
        self.register_macros('macros', get_source('macros.html'))
        self.layout = layout
        self.title = title
        self.blocks = {}

    def register_filter(self, name, fn):
        self.env.filters[name] = fn

    def register_component(self, name, component):
        self.components[name] = component

    def register_components(self, components):
        for name, component in components.iteritems():
            args = component.get('args', {}) or {}
            if isinstance(args, list):
                args = OrderedDict(item for arg in map(dict.items, args) for item in arg)
            component['args'] = args
        self.components.update(components)
        self.generate_components()

    def register_macros(self, name, macros):
        self.macros[name] = self.env.from_string(macros)

    def register_function(self, name, fn):
        self.env.globals[name] = fn

    def generate_imports(self):
        return ''.join(['{%% import %(macros)s as %(macros)s with context %%}\n' %
            {'macros': key} for key in self.macros.keys()])

    def render_component(self, name, **kwargs):
        if name not in self.components:
            raise Exception('unknown component: "%s"' % name)
        component = self.components[name]
        nav = kwargs.pop('nav', None)
        args = self.parse_args(component, kwargs)
        if 'template' not in component:
            raise Exception('template missing for component "%s"' % name)
        template = self.env.from_string(self.generate_imports() + component['template'])
        args.update(self.macros)
        def render_fn(*contents):
            if contents:
                if not component.get('container', False):
                    raise Exception('component "%s" is not a container' % name)
                args['contents'] = self.merge(*contents)
                args['raw_contents'] = map(lambda c: self.merge(c), contents)
            else:
                args['contents'] = ''
                args['raw_contents'] = []
            html = jinja2.Markup(template.render(**args))
            return html if not nav else self.nav(text=nav)(html)
        return Component(render_fn)

    def render_layout(self):
        html = self.root_template.render(layout=self.layout, title=self.title, **self.blocks)
        return bs4.BeautifulSoup(html, 'html5lib').prettify('utf-8', escape_text)

    def set(self, name):
        def block_fn(*contents):
            self.blocks[name] = jinja2.Markup(self.merge(*contents))
        return block_fn

    @classmethod
    def parse_args(cls, component, kwargs):
        expr = dict((arg, False) for arg in kwargs.keys())
        for arg, value in kwargs.iteritems():
            if arg not in component['args']:
                raise Exception('unknown argument: "%s"' % arg)
            options = map(str.strip, component['args'][arg]['values'].split('|'))
            expression_allowed = '$expression' in options
            options = filter(lambda option: option != '$expression', options)
            match_found = any(map(lambda o: cls.validate_single(o, value), options))
            if not match_found:
                if not expression_allowed:
                    raise Exception('invalid argument: %s=%s' % (arg, repr(value)))
                if not isinstance(value, basestring):
                    raise Exception('%s: expected expresssion, got %s' % (arg, repr(value)))
                expr[arg] = True
        return {'args': kwargs.copy(), 'expr': expr}

    @classmethod
    def merge(cls, *contents):
        rendered_contents = []
        for element in contents:
            if isinstance(element, basestring):
                # rendered_contents.append(escape_text(element, angular=True).strip())
                rendered_contents.append(element.strip())
            elif isinstance(element, jinja2.Markup):
                rendered_contents.append(str(element).strip())
            # elif hasattr(element, '__call__'):
                # rendered_contents.append(str(element()).strip())
            elif isinstance(element, (Component, ComponentWrapper)):
                rendered_contents.append(str(element()).strip())
            else:
                raise Exception('cannot render element: %s' % repr(element))
        return jinja2.Markup(' '.join(rendered_contents))

    @staticmethod
    def validate_single(option, value):
        if option[0] is not '$':
            return option == value
        elif option == '$context':
            return value in ['success', 'warning', 'info', 'danger']
        elif option == '$bool':
            return isinstance(value, bool)
        elif option == '$text':
            return isinstance(value, basestring)
        elif option == '$none':
            return value is None
        return False

    def generate_components(self):
        for name, component in self.components.iteritems():
            args = component['args']
            fn_args = ', '.join([arg + '=' + arg for arg in args.iterkeys()] + ['**kwargs'])
            code = "return self.render_component('%s', %s)" % (name, fn_args)
            docstring = component.get('docstring', None)
            defaults = dict((k, v['default']) for k, v in args.iteritems() if 'default' in v)
            wrapper = ComponentWrapper(new_closure(name, args.keys(), code,
                defaults=defaults, docstring=docstring, kwargs=True, closure={'self': self}))
            setattr(self, name, wrapper)
