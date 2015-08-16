# -*- coding: utf-8 -*-

import os
import sys
import json

import logging


def path_to(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

try:
    sys.path.insert(0, path_to('../..'))
finally:
    from translucent.server import Application, shared


class App(Application):
    @classmethod
    def setup(cls):
        cls.data = json.load(open(path_to('imdb.json')))
        cls.index = {title['tconst']: title for title in cls.data}

    def initialize(self):
        self.context.set_value('selected', self.data[0]['tconst'], _auto_add=True)
        self.send('value', {'key': 'selected', 'value': self.context.get_value('selected')})

    @shared
    def titles(self, env):
        return [dict(id=title['tconst'],
                     title=title['title'],
                     year=title['year'],
                     rating='{:.1f}'.format(title['rating']),
                     image=title['image']['url'].replace('@._V1_', '@._V1_SX101_AL_'))
                for title in self.data]

    @shared
    def title(self, env):
        return self.index[env.selected] if env.selected else {}


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger('translucent').setLevel(logging.DEBUG)

    App.start(path_to('imdb.js'), stylesheet=path_to('imdb.css'),
              title='IMDB Top 250', debug=True)

if __name__ == '__main__':
    main()
