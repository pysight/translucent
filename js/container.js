import React from 'react';

import Store from './store';
import log from './log';

class Container extends React.Component {
    static propTypes = {
        render: React.PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        this.env = Store.getEnv();
    }

    componentDidMount() {
        Store.listen(this.onChange);
    }

    componentWillUnmount() {
        Store.unlisten(this.onChange);
    }

    onChange = () => {
        log('Container::onChange');
        this.setState(Store.getEnv());
    }

    render() {
        log('Container::render');
        console.log(this.env);
        return <div>{this.props.render(this.env)}</div>;
    }
}

export default Container;
