# -*- coding: utf-8 -*-

import bs4
from bs4.element import (Tag, NavigableString,
    EntitySubstitution, AttributeValueWithCharsetSubstitution)
import jinja2

from .utils import is_string, to_json


def attr_if(condition, attribute, value=None):
    if not condition:
        return u''
    if not is_string(attribute):
        raise Exception('attribute name must be a string')
    if not is_string(value) and value is not None:
        raise Exception('attribute value must be a string or None')
    if value is not None:
        return ' %s="%s"' % (attribute, value)
    else:
        return ' %s' % attribute


@jinja2.contextfunction
def class_fmt(context, default, **kwargs):
    if len(kwargs) is 0:
        return '' if not default else 'class="%s"' % default
    is_expr = context['expr']
    args = context['args']
    any_expr = any(is_expr.values())
    parse_string = lambda fmt, v: fmt % v
    parse_dict = lambda fmt, v: fmt[v] if v in fmt else fmt['?']
    if any_expr:
        if len(kwargs) is 1:
            arg, fmt = kwargs.items()[0]
            if isinstance(fmt, dict):
                return 'ng-class="%s|map:%s"' % (args[arg], to_json(fmt))
        class_list = [default] if default else []
        var_list = []
        for arg, fmt in kwargs.iteritems():
            v = args[arg]
            if is_expr[arg]:
                if is_string(fmt):
                    class_list.append(fmt)
                    var_list.append(v)
                elif isinstance(fmt, dict):
                    class_list.append(r'%s')
                    var_list.append(r'(%s|map:%s)' % (v, to_json(fmt)))
            else:
                if is_string(fmt):
                    s = parse_string(fmt, v)
                    class_list.extend([s] if s else [])
                elif isinstance(fmt, dict):
                    s = parse_dict(fmt, v)
                    class_list.extend([s] if s else [])
            fmt_string = ' '.join(class_list)
            var_string = ':'.join(var_list)
        return 'ng-class="\'%s\'|sprintf:%s"' % (fmt_string, var_string)
    else:
        class_list = [default] if default else []
        for arg, fmt in kwargs.iteritems():
            v = args[arg]
            if is_string(fmt):
                s = parse_string(fmt, v)
                class_list.extend([s] if s else [])
            elif isinstance(fmt, dict):
                s = parse_dict(fmt, v)
                class_list.extend([s] if s else [])
        return 'class="%s"' % ' '.join(class_list)


def escape(s):
    return unicode(jinja2.escape(s))


def unescape(s):
    return jinja2.Markup(s).unescape()


def parse_angular(text, fmt_normal=None, fmt_angular=None):
    fmt_normal = fmt_normal or (lambda s: s)
    fmt_angular = fmt_angular or (lambda s: s)
    index, parts = 0, []
    while index < len(text):
        start = text.find('{{', index)
        end = text.find('}}', start + 2)
        if start is not -1 and end is not -1:
            if start is not index:
                parts.append(fmt_normal(text[index:start]))
            parts.append(fmt_angular(text[start:end + 2]))
            index = end + 2
        else:
            parts.append(fmt_normal(text[index:]))
            break
    return u''.join(parts)


def angular_unescape(text):
    return parse_angular(text, fmt_normal=escape, fmt_angular=unescape)


class TranslucentTag(Tag):

    @property
    def indent(self):
        return '  '

    @property
    def needs_indent(self):
        return not self.angular and self.name not in ['a', 'abbr', 'b', 'button', 'caption',
        'cite', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'i', 'label', 'li', 'option',
        'q', 's', 'script', 'small', 'span', 'strong', 'td', 'title', 'u']

    def decode(self, indent_level=0, **kwargs):
        attrs = []
        if self.attrs:
            for key, val in sorted(self.attrs.items()):
                if val is None:
                    decoded = key
                else:
                    if isinstance(val, list) or isinstance(val, tuple):
                        val = ' '.join(val)
                    elif not isinstance(val, basestring):
                        val = unicode(val)
                    elif isinstance(val, AttributeValueWithCharsetSubstitution):
                        val = val.encode('utf-8')
                    text = val
                    decoded = (unicode(key) + '='
                        + EntitySubstitution.quoted_attribute_value(text))
                attrs.append(decoded)
        close = ''
        closeTag = ''

        prefix = ''
        if self.prefix:
            prefix = self.prefix + ":"

        if self.is_empty_element:
            close = '/'
        else:
            closeTag = '</%s%s>' % (prefix, self.name)

        parent_flatten = kwargs.pop('flatten', False)
        if not parent_flatten:
            tag_needs_indent = lambda tag: isinstance(tag, Tag) and tag.needs_indent
            indent_contents = len(self.find_all(tag_needs_indent)) > 0
            flatten = not self.needs_indent and not indent_contents
        else:
            flatten = True

        pretty_print = self._should_pretty_print(indent_level)
        space = ''
        indent_space = ''
        if indent_level is not None:
            indent_space = (self.indent * (indent_level - 1))
        if pretty_print:
            space = indent_space
            indent_contents = indent_level + 1
        else:
            indent_contents = None
        contents = self.decode_contents(indent_contents, flatten=flatten)

        if self.hidden:
            s = contents
        else:
            s = []
            attribute_string = ''
            if attrs:
                attribute_string = ' ' + ' '.join(attrs)
            if indent_level is not None and not parent_flatten:
                s.append(indent_space)
            s.append('<%s%s%s%s>' % (
                prefix, self.name, attribute_string, close))
            if pretty_print and not flatten:
                s.append('\n')
            s.append(contents)
            if pretty_print and contents and contents[-1] != '\n' and not flatten:
                s.append('\n')
            if pretty_print and closeTag and not flatten:
                s.append(space)
            s.append(closeTag)
            if indent_level is not None and closeTag and not parent_flatten:
                s.append('\n')
            s = ''.join(s)
        return u'' + s

    def decode_contents(self, indent_level=0, **kwargs):
        flatten = kwargs.pop('flatten', False)
        pretty_print = indent_level is not None
        s = []
        for c in self:
            text = None
            if isinstance(c, NavigableString):
                text = c.output_ready(angular_unescape)
            elif isinstance(c, TranslucentTag):
                s.append(c.decode(indent_level, flatten=flatten))
            if text and indent_level and not self.name == 'pre':
                text = text.strip()
            if text:
                if pretty_print and not self.name == 'pre' and not flatten:
                    s.append(self.indent * (indent_level - 1))
                s.append(text)
                if pretty_print and not self.name == 'pre' and not flatten:
                    s.append('\n')
        return ''.join(s)

bs4.Tag = TranslucentTag


class TranslucentSoup(TranslucentTag, bs4.BeautifulSoup):

    def prettify(self, **kwargs):
        return super(TranslucentSoup, self).decode().encode('utf-8', 'xmlcharrefreplace')


def format_page(html):
    return TranslucentSoup(html).prettify()
