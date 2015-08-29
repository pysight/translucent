import _ from 'underscore';

import alt from './alt';
import actions from './actions';
import log from './log';

class Store {
    static displayName = 'Store';

    constructor() {
        this.env = {};
        this.update = null;
        this.bindListeners({
            onChange: actions.UPDATE_ENV
        });
        this.exportPublicMethods({
            getEnv: () => this.env,
            getUpdate: () => this.update
        });
    }

    onChange({key, value, serverside}) {
        log('Store::onChange', {key, value, serverside});
        if (_.isEqual(this.env[key], value)) {
            return false;
        }
        let update = {};
        update[key] = value;
        this.env = Object.assign(this.env, update);
        this.update = {key, value, serverside};
    }
}

export default alt.createStore(Store);
