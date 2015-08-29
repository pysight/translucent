import _ from 'underscore';
import SockJS from 'sockjs-client';

import log from './log';
import Store from './store';
import actions from './actions';

const Message = {
    VALUE: 'value',
    READY: 'ready'
};

class Connection {
    constructor() {
        this.callback = _.noop;
        this.conn = new SockJS(`http://${window.location.host}/api`);
        this.conn.onopen = () => Store.listen(this.onStoreUpdate);
        this.conn.onclose = () => Store.unlisten(this.onStoreUpdate);
        this.conn.onmessage = this.onMessageReceived;
    }

    sendMessage(data) {
        this.conn.send(JSON.stringify(data));
    }

    onStoreUpdate = () => {
        let update = Store.getState().update;
        if (update && !update.serverside) {
            log('Connection::onStoreUpdate', update);
            this.sendMessage({
                kind: Message.VALUE,
                data: {
                    key: update.key,
                    value: update.value
                }
            });
        }
    }

    onMessageReceived = (msg) => {
        const {kind, data} = JSON.parse(msg.data);
        log('Connection::onMessage', kind, data);
        if (kind === Message.VALUE) {
            actions.updateEnv({
                key: data.key,
                value: data.value,
                serverside: true
            });
        } else if (kind === Message.READY) {
            this.callback();
        }
    }
}

export default _.once(() => {
    let connection = new Connection();
    return {
        then: callback => {
            connection.callback = callback;
        }
    };
});

