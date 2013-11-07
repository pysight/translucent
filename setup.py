#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='translucent',
    version='0.0.2',
    description='translucent',
    long_description=open('README.rst', 'rt').read(),
    author='Ivan Smirnov',
    author_email='i.s.smirnov@gmail.com',
    packages=['translucent'],
    install_requires=[
        'Flask==0.10.1',
        'Werkzeug==0.9.4',
        'Jinja2==2.7.1',
        'gevent==0.13.8',
        'gevent-socketio==0.3.5-rc2',
        'beautifulsoup4==4.3.2',
        'html5lib==1.0b3',
        'flake8==2.1.0',
        'nose==1.3.0',
        'coverage==3.7'
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
