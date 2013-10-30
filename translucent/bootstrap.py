# -*- coding: utf-8 -*-

import yaml

from .ui import RenderEngine


class BootstrapUI(RenderEngine, object):

    def __init__(self, *args, **kwargs):
        super(BootstrapUI, self).__init__(*args, **kwargs)
        self.register_components('components/bootstrap.yml')