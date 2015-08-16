require('react-select/dist/default.css');
import { default as ReactSelect } from 'react-select';

import Actions from './actions';
import Store from './store';

import debug from 'debug';
const log = debug('translucent');

class BindableComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {value: Store.getInitialState()[this.props.bind]};
    }

    updateValue(env, key) {
        if (key == this.props.bind || !key) {
            this.setState({value: env[this.props.bind]});
        }
    }

    componentDidMount() {
        this.unsubscribe = Store.listen(this.updateValue.bind(this), this);
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    onValueChange(value) {
        Actions.updateEnv(this.props.bind, value, true);
    }
}

window.BindableComponent = BindableComponent;

class Select extends BindableComponent {
    onChange(value) {
        if (this.props.onChange) {
            this.props.onChange(value);
        }
        this.onValueChange(value);
    }

    render() {
        let {options} = this.props;
        const props = _.pick(this.props, (v, k) => k != 'bind' && k != 'options');

        if (_.isArray(options)) {
            options = _.map(options, v => _.isString(v) ? {value: v, label: v} : v);
        }
        else if (_.isObject(options)) {
            options = _.map(_.keys(options).sort(), v => ({value: v, label: options[v]}));
        }
        return <ReactSelect {...props} options={options} value={this.state.value}
                            onChange={this.onChange.bind(this)}/>;
    }
}

window.Select = Select;
