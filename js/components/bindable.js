import React from 'react';

import Store from '../store';
import actions from '../actions';

class BindableComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {value: Store.getState().env.get(this.props.bind)};
    }

    onStoreUpdate = () => {
        const key = Store.getState().update.key;
        if (key === this.props.bind || !key) {
            this.setState({value: Store.getState().env.get(this.props.bind)});
        }
    }

    componentDidMount() {
        Store.listen(this.onStoreUpdate);
    }

    componentWillUnmount() {
        Store.unlisten(this.onStoreUpdate);
    }

    updateValue(value) {
        actions.updateEnv({
            key: this.props.bind,
            value: value
        });
    }
}

export default BindableComponent;
