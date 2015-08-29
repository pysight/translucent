import React from 'react';

import log from './log';
import Store from './store';

class Container extends React.Component {
    static propTypes = {
        render: React.PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        this.state = {env: Store.getState().env};
    }

    componentDidMount() {
        Store.listen(this.onStoreUpdate);
    }

    componentWillUnmount() {
        Store.unlisten(this.onStoreUpdate);
    }

    shouldComponentUpdate(nextProps, nextState) {
        return this.state.env !== nextState.env;
    }

    onStoreUpdate = () => {
        log('Container::onStoreUpdate');
        this.setState({env: Store.getState().env});
    }

    render() {
        log('Container::render');
        return <div>{this.props.render(this.state.env.toJS())}</div>;
    }
}

export default Container;
