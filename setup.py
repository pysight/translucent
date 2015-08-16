# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='translucent',
    version='0.2',
    author='Ivan Smirnov',
    author_email='i.s.smirnov@gmail.com',
    packages=['translucent'],
    install_requires=[
        'six',
        'joblib',
        'tornado',
        'sockjs-tornado'
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intented Audience :: Developers',
        'Framework :: Tornado',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
        'Topic :: WWW/HTTP :: Dynamic Content'
    ]
)
