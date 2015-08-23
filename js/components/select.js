import _ from 'underscore';
import Select from 'react-select';
import 'react-select/dist/default.css';

import BindableComponent from './bindable';

class ReactSelect extends BindableComponent {
    onChange = (value) => {
        if (this.props.onChange) {
            this.props.onChange(value);
        }
        this.onValueChange(value);
    }

    render() {
        let {options} = this.props;
        const props = _.pick(this.props, (v, k) => k !== 'bind' && k !== 'options');

        if (_.isArray(options)) {
            options = options.map(v => _.isString(v) ? {value: v, label: v} : v);
        } else if (_.isObject(options)) {
            options = _.keys(options).sort().map(v => ({value: v, label: options[v]}));
        }
        return <Select options={options} value={this.state.value}
                       onChange={this.onChange} {...props} />;
    }
}

export default ReactSelect;
