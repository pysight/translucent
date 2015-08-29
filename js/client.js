import React from 'react';

import Container from './container';

export function render(func) {
    React.render(<Container render={func} />, document.body);
}
