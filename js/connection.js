import SockJS from 'sockjs-client';
import { updateEnv } from './actions';
import Store from './store';
import log from './log';

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
        this.conn.onopen = this.onOpen.bind(this);
        this.conn.onclose = this.onClose.bind(this);
        this.conn.onmessage = this.onMessage.bind(this);
        this.ready = false;
    }

    send(data) {
        this.conn.send(JSON.stringify(data));
    }

    onOpen() {
        log('Connection::onOpen');
        this.unsubscribe = Store.listen(this.sendValue.bind(this), this);
    }

    onClose() {
        log('Connection::onClose');
        this.unsubscribe();
    }

    sendValue(env, key, client) {
        log('Connection::sendValue', env, key, client);
        if (client) {
            this.send({kind: 'value', data: {key: key, value: env[key]}});
        }
    }

    onMessage(msg) {
        const {kind, data} = JSON.parse(msg.data);
        log('Connection::onMessage', kind, data);
        if (kind === 'value') {
            // use synchronous actions triggers before the store is fully populated
            const trigger = this.ready ? updateEnv : updateEnv.trigger;
            trigger.call(updateEnv, data.key, data.value, false);
        } else if (kind === 'ready') {
            this.ready = true;
            this.callback();
        }
    }
}
