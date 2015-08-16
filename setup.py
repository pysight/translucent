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
        'tornado >= 4.0',
        'sockjs-tornado'
    ],
    package_data={
        'translucent': ['static/*.*', 'static/fonts/*.*']
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intented Audience :: Developers',
        'Framework :: Tornado',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
