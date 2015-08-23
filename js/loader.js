import React from 'react';
import _ from 'underscore';

export default function(code) {
    function func(require) { // eslint-disable-line no-unused-vars
        eval(code);
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
