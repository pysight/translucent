# -*- coding: utf-8 -*

import os
import execjs


def get_js_runtime():
    try:
        return execjs.get('Node')
    except execjs.RuntimeUnavailable:
        try:
            return execjs.get('PhantomJS')
        except execjs.RuntimeUnavailable:
            return None


def transpile_jsx(code):
    runtime = get_js_runtime()
    if runtime is None:
        raise RuntimeError('JavaScript runtime not available')
    dirname = os.path.abspath(os.path.dirname(__file__))
    babel_path = os.path.join(dirname, 'static', 'babel-transform.js')
    context = runtime.compile("""
        babel = require('%s');
        function transform(code) { return babel(code, {stage: 0}).code; }
    """ % babel_path)
    return context.call('transform', code)
