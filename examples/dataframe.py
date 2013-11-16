# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import json
from translucent import Server, App, BootstrapUI

ui = BootstrapUI('bootstrap-sidebar', 'DataFrame Test App')
ui.set('top')(ui.header('Translucent', 'Reactive Demo: LoL Champions'))
ui.set('left')(ui.form[
    ui.select('tag1', 't for t in env.tags1', placeholder='(all)', label='First tag:'),
    ui.select('tag2', 't for t in env.tags2', placeholder='(all)', label='Second tag:')])
ui.set('right')(ui.panel[ui.dataframe('table')])


class DataframeApp(App):

    @classmethod
    def on_start(cls):
        with open('dataframe.json') as f:
            cls.df = pd.DataFrame.from_dict(json.load(f))
            cls.df.id = cls.df.id.astype(int).apply(lambda x: '#%03d' % x)
            cls.df = cls.df.set_index('id')[['name', 'tags']]
            cls.tags = cls.df.tags.copy()
            cls.df.tags = cls.df.tags.apply(lambda tags: ', '.join(tags))

    def table(self, env):
        match = self.df.tags.str.contains
        return self.df[match(env.tag1 or '') & match(env.tag2 or '')]

    def get_tags(self, env, other):
        tags = self.tags.ix[env.table.index].tolist()
        return [] if not tags else sorted(set(np.concatenate(tags)) - set([other]))

    def on_init(self):
        self.reactive('table', self.table)
        self.reactive('tags1', lambda env: self.get_tags(env, env.tag2), shared=True)
        self.reactive('tags2', lambda env: self.get_tags(env, env.tag1), shared=True)
        self.set_input('tag1', None)
        self.set_input('tag2', None)
        self.link('table')

Server(DataframeApp, ui, host='0.0.0.0', port=5000).run()
