import _ from 'underscore';
import Immutable from 'immutable';
import immutable from 'alt/utils/ImmutableUtil';

import log from './log';
import alt from './alt';
import actions from './actions';

@immutable
class Store {
    static displayName = 'Store';

    constructor() {
        this.update = null;
        this.env = new Immutable.Map();
        this.bindListeners({
            onChange: actions.UPDATE_ENV
        });
    }

    onChange({key, value, serverside}) {
        log('Store::onChange', {key, value, serverside});
        if (_.isEqual(this.env.get(key), value)) {
            return false;
        }
        this.env = this.env.set(key, value);
        this.update = {key, value, serverside};
    }
}

export default alt.createStore(Store);
