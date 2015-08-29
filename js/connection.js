import SockJS from 'sockjs-client';

import log from './log';
import Store from './store';
import actions from './actions';

const Message = {
    VALUE: 'value',
    READY: 'ready'
};

const $instance = Symbol();

export default class Connection {
    constructor(callback) {
        if (Connection[$instance]) {
            return Connection[$instance];
        } else {
            Connection[$instance] = this;
        }
        this.conn = new SockJS(`http://${window.location.host}/api`);
        this.callback = callback;
        this.conn.onopen = this.onOpen;
        this.conn.onclose = this.onClose;
        this.conn.onmessage = this.onMessage;
        this.ready = false;
    }

    send(data) {
        this.conn.send(JSON.stringify(data));
    }

    onOpen = () => {
        log('Connection::onOpen');
        Store.listen(this.onChange);
    }

    onClose = () => {
        log('Connection::onClose');
        Store.unlisten(this.onChange);
    }

    onChange = () => {
        let update = Store.getState().update;
        if (update && !update.serverside) {
            log('Connection::onChange', update);
            this.send({
                kind: Message.VALUE,
                data: {
                    key: update.key,
                    value: update.value
                }
            });
        }
    }

    onMessage = (msg) => {
        const {kind, data} = JSON.parse(msg.data);
        log('Connection::onMessage', kind, data);
        if (kind === Message.VALUE) {
            actions.updateEnv({
                key: data.key,
                value: data.value,
                serverside: true
            });
        } else if (kind === Message.READY) {
            this.ready = true;
            this.callback();
        }
    }
}
