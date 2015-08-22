import React from 'react';
import _ from 'underscore';
import { transform } from 'react-tools';

export default function(code) {
    const es5 = transform(code, {harmony: true});
    function func(require) { // eslint-disable-line no-unused-vars
        eval(es5);
    }
    require.ensure([], require => {
        return func(req => {
            if (req === 'react') {
                return React;
            } else if (req === 'underscore') {
                return _;
            } else if (req === 'jquery') {
                return require('jquery');
            } else if (req === 'classnames') {
                return require('classnames');
            } else if (req === 'react-bootstrap') {
                return require('react-bootstrap');
            } else if (req === 'bootstrap') {
                require('bootstrap');
            }
        });
    }, 'extras');
}
