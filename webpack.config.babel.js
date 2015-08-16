import path from 'path';
import webpack from 'webpack';

const STATIC = path.join(__dirname, 'translucent/static');
const NPM = path.join(__dirname, 'node_modules');

let config = {
    entry: {
        app: [`${__dirname}/js/app.js`],
        vendor: [
            'react', 'react-tools', 'reflux', 'sockjs-client', 'jquery', 'underscore', 'debug',
            'react-select', 'react-input-autosize', 'classnames'
        ]
    },
    output: {
        path: STATIC,
        publicPath: '/static/',
        filename: '[name].bundle.js',
        chunkFilename: '[name].bundle.js'
    },
    module: {
        loaders: [
            { test: /\.css$/, loader: 'style!css' },
            { test: /\.less$/, loader: 'style!css!less' },
            { test: /\.js$/, exclude: /node_modules/, loader: 'babel' },
            { test: /react\-bootstrap\/lib\/index\.js$/, loader: 'bundle?lazy&name=extras' },
            { test: /bootstrap\/dist\/js\/npm\.js$/, loader: 'bundle?lazy&name=extras' }
        ],
        noParse: []
    },
    resolve: {
        extensions: ['', '.js'],
        modulesDirectories: ['node_modules'],
        alias: {
            'react-select.less': `${NPM}/react-select/less/select.less`
        }
    },
    node: {
        fs: 'empty', net: 'empty', tls: 'empty', process: 'empty'
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            'root.jQuery': 'jquery',
            React: 'react',
            Reflux: 'reflux',
            _: 'underscore'
        }),
        new webpack.DefinePlugin({
            'process.env': {
                NODE_ENV: JSON.stringify('production')
            }
        }),
        new webpack.optimize.CommonsChunkPlugin('vendor', 'vendor.bundle.js', Infinity)
    ],
};

if (process.env.NODE_ENV == 'production') {
    config.plugins.push(
        new webpack.optimize.DedupePlugin(),
        new webpack.optimize.UglifyJsPlugin({
            sourceMaps: false,
            minimize: true,
            compress: {
                warnings: false
            },
            output: {
                comments: false,
                semicolons: true
            }
        })
    );
} else {
    config.devtool = 'eval-cheap-module-source-map';
}

export default config;
