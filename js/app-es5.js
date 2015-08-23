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

const evalJSX = defer(2, loader);

const connection = new Connection(evalJSX);

fetch('/index.js')
    .then(response => response.text())
    .then(body => evalJSX(body));
