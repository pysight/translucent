# -*- coding: utf-8 -*-

import re

from .ui import RenderEngine


class BootstrapUI(RenderEngine):

    def __init__(self, *args, **kwargs):
        super(BootstrapUI, self).__init__(*args, **kwargs)
        self.register_components('components/bootstrap.yml')
        self.register_value_type('$context', ['primary', 'success', 'info',
            'warning', 'danger'])
        self.register_value_type('$icon',
            lambda s: bool(re.match(r'^fa\-[a-z\-]+$', s)))
