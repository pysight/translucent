# -*- coding: utf-8 -*-

import bs4
from bs4.element import (Tag, NavigableString,
    EntitySubstitution, AttributeValueWithCharsetSubstitution)
import jinja2

from .utils import is_string, is_number


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
        return '[%s]' % sep[0].join([to_json(elem) for elem in obj])
    elif isinstance(obj, dict):
        return '{%s}' % sep[0].join(['%s%s%s' %
            (quote(k), sep[1], to_json(v)) for k, v in obj.iteritems()])
    raise Exception('cannot convert to json: "%s"' % str(obj))


def attr_if(condition, attribute, value):
    if not is_string(attribute):
        raise Exception('attribute name must be a string')
    if not is_string(value):
        raise Exception('attribute value must be a string')
    if condition:
        return ' %s="%s"' % (attribute, value)
    return ''

def class_if(condition, value):
    if not is_string(attribute):
        raise Exception('attribute name must be a string')
    if not is_string(value):
        raise Exception('attribute value must be a string')
    if condition:
        return ' %s="%s"' % (attribute, value)
    return ''

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
    def need_indent(self):
        return not self.angular and self.name not in ['a', 'abbr', 'b', 'button',
        'caption', 'cite', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'i', 'li',
        'option', 'q', 's', 'small', 'span', 'strong', 'td', 'u']

    @property
    def is_angular(self):
        return self.name == 'script' and self.attrs.get('type') == 'ng'

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

        need_indent = self.need_indent

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
        contents = self.decode_contents(indent_contents, need_indent=need_indent)

        if self.hidden or self.is_angular:
            s = contents
        else:
            s = []
            attribute_string = ''
            if attrs:
                attribute_string = ' ' + ' '.join(attrs)
            if indent_level is not None:
                s.append(indent_space)
            s.append('<%s%s%s%s>' % (
                    prefix, self.name, attribute_string, close))
            if pretty_print:
                s.append('\n')
            s.append(contents)
            if pretty_print and contents and contents[-1] != '\n':
                s.append('\n')
            if pretty_print and closeTag:
                s.append(space)
            s.append(closeTag)
            if indent_level is not None and closeTag:
                s.append('\n')
            s = ''.join(s)
        return u'' + s

    def decode_contents(self, indent_level=0, **kwargs):

        need_indent = kwargs.pop('need_indent', False)
        pretty_print = indent_level is not None
        s = []
        for c in self:
            text = None
            if isinstance(c, NavigableString):
                text = c.output_ready(angular_unescape)
            elif isinstance(c, TranslucentTag):
                s.append(c.decode(indent_level))
            if text and indent_level and not self.name == 'pre':
                text = text.strip()
            if text:
                if pretty_print and not self.name == 'pre':
                    s.append(self.indent * (indent_level - 1))
                s.append(text)
                if pretty_print and not self.name == 'pre':
                    s.append('\n')
        return ''.join(s)

bs4.Tag = TranslucentTag

class TranslucentSoup(TranslucentTag, bs4.BeautifulSoup):

    def prettify(self, **kwargs):
        return super(TranslucentSoup, self).decode().encode('utf-8', 'xmlcharrefreplace')

def format_page(html):
    return TranslucentSoup(html).prettify()
