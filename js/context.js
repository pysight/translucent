import { Component } from 'react';
import Store from './store';
import log from './log';

export default class Context extends Component {
    constructor(props) {
        super(props);
        this.state = {env: Store.getInitialState()};
        log('Context::constructor', this.state.env);
    }

    render() {
        log('Context::render', this.state.env);
        return <div>{this.props.render(this.state.env)}</div>;
    }

    updateEnv(env) {
        log('Context::updateEnv', env);
        this.setState({env});
    }

    componentDidMount() {
        this.unsubscribe = Store.listen(::this.updateEnv, this);
    }

    componentWillUnmount() {
        this.unsubscribe();
    }
}
