import React from 'react';

import Connection from './connection';
import Context from './context';
import Store from './store';
import defer from './defer';
import loader from './loader';

export default function app(transformer) {
    window.Translucent = {
        render: (func) => {
            React.render(<Context render={func} />, document.body);
        }
    };

    Store.getInitialState();

    const evalJSX = defer(2, data => loader((transformer || (x => x))(data)));

    const connection = new Connection(evalJSX);

    fetch('/index.js')
        .then(response => response.text())
        .then(body => evalJSX(body));
}
