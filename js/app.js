import { transform } from 'react-tools';

import Connection from './connection';
import Context from './context';
import Store from './store';
import syncCallback from './syncCallback';
import log from './log';

import './components';

window['_'] = _;

window['req'] = function (mods, cb) {
    let callback = syncCallback(1 + mods.length, cb);
    for (let mod of mods) {
        if (mod == 'bootstrap') {
            require('bootstrap')(mod => {
                callback();
            });
        }
        if (mod == 'react-bootstrap') {
            require('react-bootstrap')(mod => {
                window.ReactBootstrap = mod;
                callback();
            });
        } else if (mod == 'classnames') {
            require('classnames')(mod => {
                window.classNames = mod;
                callback();
            });
        }
    }
    callback();
}
window.Translucent = {
    render: (func) => {
        React.render(<Context render={func} />, document.body);
    }
}

// initialize the store
Store.getInitialState();

// the callback will be triggered on the second time it's called
const evalJSX = syncCallback(2, data => eval(transform(data, { harmony: true })));

// initialize SockJS connection
const connection = new Connection(evalJSX);

// fetch user code from the server and execute when ready
$.ajax({
    url: 'index.js',
    cache: false,
    converters: { 'text script': _.identity },
    success: evalJSX
});
