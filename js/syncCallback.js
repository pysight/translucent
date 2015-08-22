class SyncCallback {
    constructor(times, func) {
        this.called = 0;
        this.times = times;
        this.func = func;
        this.data = null;
    }

    callback(data) {
        this.called += 1;
        this.data = this.data || data;
        if (this.called === this.times) {
            return this.func(this.data);
        }
    }
}

export default (times, func) => ::(new SyncCallback(times, func)).callback;
