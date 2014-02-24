#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='translucent',
    version='0.0.4',
    description='translucent',
    long_description=open('README.rst', 'rt').read(),
    author='Ivan Smirnov',
    author_email='i.s.smirnov@gmail.com',
    packages=['translucent', 'translucent.tests'],
    install_requires=[
        'six==1.5.2',
        'mock==1.0.1',
        'ordereddict==1.1',
        'PyYAML==3.10',
        'joblib==0.7.1',
        'greenlet==0.4.2',
        'gevent==1.0',
        'gevent-socketio==0.3.6',
        'gevent-websocket==0.9.2',
        'Werkzeug==0.9.4',
        'Jinja2==2.7.2',
        'Flask==0.10.1',
        'beautifulsoup4==4.3.2',
        'html5lib==1.0b3',
        'pytest==2.5.2'
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intented Audience :: Developers',
        'Framework :: Flask',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: WWW/HTTP :: Dynamic Content'
    ]
)
