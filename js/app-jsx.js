import app from './app';

require.ensure([], require => {
    const transform = require('babel-transform').transform;
    app(data => transform(data, {stage: 0}).code);
}, 'babel');
