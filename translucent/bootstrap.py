# -*- coding: utf-8 -*-

import yaml

from .ui import RenderEngine


class BootstrapUI(RenderEngine):

    def __init__(self, *args, **kwargs):
        super(BootstrapUI, self).__init__(*args, **kwargs)
        self.register_components('components/bootstrap.yml')
        self.register_value_type('$context', ['primary', 'success', 'info',
            'warning', 'danger'])