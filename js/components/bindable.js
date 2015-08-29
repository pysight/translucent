import React from 'react';

import Store from '../store';
import actions from '../actions';

class BindableComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {value: Store.getEnv()[this.props.bind]};
    }

    onValueUpdate = () => {
        const key = Store.getState().update.key;
        const env = Store.getEnv();
        if (key === this.props.bind || !key) {
            this.setState({value: env[this.props.bind]});
        }
    }

    componentDidMount() {
        this.listener = Store.listen(this.onValueUpdate);
    }

    componentWillUnmount() {
        this.listener.unlisten();
    }

    onValueChange(value) {
        actions.updateEnv({
            key: this.props.bind,
            value: value
        });
    }
}

export default BindableComponent;
