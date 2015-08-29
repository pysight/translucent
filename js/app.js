import React from 'react';

import defer from './defer';
import loader from './loader';
import Connection from './connection';
import Container from './container';

export default function app(transformer) {
    window.Translucent = {
        render: (func) => {
            React.render(<Container render={func} />, document.body);
        }
    };

    const evalJSX = defer(2, data => loader((transformer || (x => x))(data)));

    const connection = new Connection(evalJSX);

    fetch('/index.js')
        .then(response => response.text())
        .then(body => evalJSX(body));
}
