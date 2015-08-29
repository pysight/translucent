import _ from 'underscore';

import defer from './defer';
import loader from './loader';
import connect from './connect';

export default function app(transformer) {
    const codeLoader = _.compose(loader, transformer || _.identity);
    const evalUserCode = defer(2, codeLoader);
    connect().then(evalUserCode);
    fetch('/index.js').then(r => r.text()).then(evalUserCode);
}
