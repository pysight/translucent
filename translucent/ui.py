# -*- coding: utf-8 -*-

import jinja2
import yaml
import inspect
import bs4


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


class BootstrapUI:

    def __init__(self, layout=None, title=''):
        loader = jinja2.PackageLoader(__package__, '../templates')
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
        self.components.update(components)

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
                args['contents'] = self.merge(contents)
                args['raw_contents'] = map(lambda c: self.merge([c]), contents)
            else:
                args['contents'] = ''
                args['raw_contents'] = []
            html = jinja2.Markup(template.render(**args))
            return html if not nav else self.nav(text=nav)(html)
        return render_fn

    def render_layout(self):
        html = self.root_template.render(layout=self.layout, title=self.title, **self.blocks)
        return bs4.BeautifulSoup(html, 'html5lib').prettify('utf-8', self.escape_text)

    def set(self, name):
        def block_fn(*contents):
            self.blocks[name] = jinja2.Markup(self.merge(contents))
        return block_fn

    @classmethod
    def parse_args(cls, component, kwargs):
        expr = dict((arg, False) for arg in kwargs.keys())
        for arg, value in kwargs.iteritems():
            if arg not in component['args']:
                raise Exception('unknown argument: "%s"' % arg)
            options = map(str.strip, component['args'][arg].split('|'))
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
    def merge(cls, contents):
        rendered_contents = []
        for element in contents:
            if isinstance(element, basestring):
                # rendered_contents.append(cls.escape_text(element, angular=True).strip())
                rendered_contents.append(element.strip())
            elif isinstance(element, jinja2.Markup):
                rendered_contents.append(str(element).strip())
            elif hasattr(element, '__call__'):
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

    @staticmethod
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

    @classmethod
    def get_args(cls):
        pos_name, kw_name, args = inspect.getargvalues(inspect.stack()[1][0])[-3:]
        args.update(args.pop(kw_name, []))
        return dict((k, v) for k, v in args.iteritems() if not isinstance(v, cls))

    ###########################################################################

    def panel(self, header=None, footer=None, title=False, style='default', **kwargs):
        return self.render_component('panel', **self.get_args())

    def h1(self, **kwargs):
        return self.render_component('h1', **self.get_args())

    def p(self, **kwargs):
        return self.render_component('p', **self.get_args())

    def list(self, style='default', data=None, **kwargs):
        return self.render_component('list', **self.get_args())

    def nav(self, text, **kwargs):
        return self.render_component('nav', **self.get_args())

    def navlist(self, **kwargs):
        return self.render_component('navlist', **self.get_args())

    def header(self, title=None, subtitle=None, size='default', **kwargs):
        return self.render_component('header', **self.get_args())

    def well(self, size='default', **kwargs):
        return self.render_component('well', **self.get_args())
