import { transform } from 'react-tools';

import Connection from './connection';
import Context from './context';
import Actions from './actions';
import Store from './store';
import Components from './components';

import debug from 'debug';
debug.enable('translucent');
const log = debug('translucent');

class SyncCallback {
    constructor(times, func) {
        this.called = 0;
        this.times = times;
        this.func = func;
    }

    callback(data) {
        this.called += 1;
        this.data = this.data || data;
        if (this.called == this.times) {
            this.func(this.data);
        }
    }
}

$(() => {
    window['_'] = _;

    window['req'] = function (mods, cb) {
        let sc = new SyncCallback(1 + mods.length, cb);
        for (let mod of mods) {
            if (mod == 'bootstrap') {
                require('bootstrap')(mod => {
                    sc.callback();
                });
            }
            if (mod == 'react-bootstrap') {
                require('react-bootstrap')(mod => {
                    window.ReactBootstrap = mod;
                    sc.callback();
                });
            } else if (mod == 'classnames') {
                require('classnames')(mod => {
                    window.classNames = mod;
                    sc.callback();
                });
            }
        }
        sc.callback();
    }
    window.Translucent = {
        render: (func) => {
            React.render(<Context render={func} />, document.body);
        }
    }

    // initialize the store
    Store.getInitialState();

    const sync = new SyncCallback(2, data => {
        eval(transform(data, {harmony: true}));
    });

    // initialize SockJS connection
    const connection = new Connection(sync.callback.bind(sync));

    // fetch user code from the server and execute when ready
    $.ajax({
        url: 'index.js',
        cache: false,
        converters: { 'text script': _.identity },
        success: sync.callback.bind(sync)
    });
});
