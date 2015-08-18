class SyncCallback {
    constructor(times, func) {
        this.called = 0;
        this.times = times;
        this.func = func;
    }

    callback(data) {
        this.called += 1;
        this.data = this.data || data;
        if (this.called === this.times) {
            this.func(this.data);
        }
    }
}

export default (times, func) => {
    let sync = new SyncCallback(times, func);
    return sync.callback.bind(sync);
};
