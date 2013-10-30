# -*- coding: utf-8 -*-

import jinja2
import yaml
import bs4
from collections import OrderedDict

from .utils import tojson, escape_text, new_closure, is_valid_name


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


class RenderEngine:

    def __init__(self, layout=None, title=''):
        try:
            self.loader = jinja2.PackageLoader(__package__, '../templates')
        except:
            self.loader = jinja2.FileSystemLoader('../templates')
        self.env = jinja2.Environment(loader=self.loader)
        self.root_template = self.env.get_template('index.html')
        self.components = {}
        self.register_components('components/default.yml')
        self.register_filter('tojson', tojson)
        self.macros = {}
        self.register_macros('macros', self.load_source('macros.html'))
        self.layout = layout
        self.title = title
        self.blocks = {}

    def load_source(self, path):
        return self.loader.get_source(self.env, path)[0]

    def register_filter(self, name, fn):
        self.env.filters[name] = fn

    def register_components(self, components):
        if isinstance(components, basestring):
            components = yaml.load(self.load_source(components))
        for name, component in components.iteritems():
            if not is_valid_name(name):
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

    def render_component(self, name, **kwargs):
        if name not in self.components:
            raise Exception('unknown component: "%s"' % name)
        component = self.components[name]
        nav = kwargs.pop('nav', None)
        args = self.parse_args(component, kwargs)
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

    @staticmethod
    def merge(*contents):
        rendered_contents = []
        for element in contents:
            if isinstance(element, basestring):
                s = element
            elif isinstance(element, jinja2.Markup):
                s = str(element)
            elif isinstance(element, Component):
                s = str(element())
            elif isinstance(element, ComponentWrapper):
                s = str(element()())
            else:
                raise Exception('cannot render element: %s' % repr(element))
            rendered_contents.append(str(s).strip())
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
