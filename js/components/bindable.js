import React from 'react';

import Store from '../store';
import { updateEnv } from '../actions';

class BindableComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {value: Store.getInitialState()[this.props.bind]};
    }

    onValueUpdate = (env, key) => {
        if (key === this.props.bind || !key) {
            this.setState({value: env[this.props.bind]});
        }
    }

    componentDidMount() {
        this.unsubscribe = Store.listen(this.onValueUpdate, this);
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    onValueChange(value) {
        updateEnv(this.props.bind, value, true);
    }
}

export default BindableComponent;
