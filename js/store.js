import Reflux from 'reflux';
import Actions from './actions';
import log from './log';

export default Reflux.createStore({
    listenables: [Actions],

    onUpdateEnv: function(key, value, client) {
        log('Store::onUpdateEnv', key, value, client);
        this.env = this.env || {};
        if (!_.isEqual(this.env[key], value)) {
            this.env[key] = value;
            this.trigger(this.env, key, client);
        }
    },

    onSendAll: function() {
        log('onSendAll', this.env);
        this.trigger(this.env);
    },

    getInitialState: function() {
        this.env = this.env || {};
        return this.env;
    }
});
