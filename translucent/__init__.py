# -*- coding: utf-8 -*-


def patch_thread():
    try:
        from gevent import monkey
        import sys
        sys.modules.pop('threading', None)
        monkey.patch_thread()
    except:
        pass

patch_thread()

from .app import App, Server
from .bootstrap import BootstrapUI

__version__ = '0.0.3'

__all__ = (App, Server, BootstrapUI)
