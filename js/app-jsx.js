import React from 'react';

import Connection from './connection';
import Context from './context';
import Store from './store';
import defer from './defer';
import loader from './loader';

import './components';

window.Translucent = {
    render: (func) => {
        React.render(<Context render={func} />, document.body);
    }
};

Store.getInitialState();

require.ensure([], require => {
    const transform = require('babel-transform').transform;
    const evalJSX = defer(2, code => loader(transform(code, {stage: 0}).code));
    const connection = new Connection(evalJSX);
    fetch('/index.js')
        .then(response => response.text())
        .then(body => evalJSX(body));
}, 'babel');

