import path from 'path';
import webpack from 'webpack';

let config = {
    entry: {
        'app-es5': path.join(__dirname, 'js/app-es5'),
        'app-jsx': path.join(__dirname, 'js/app-jsx'),
        vendor: [
            'react', 'sockjs-client', 'underscore', 'debug', 'whatwg-fetch'
        ]
    },
    output: {
        path: path.join(__dirname, 'translucent/static'),
        publicPath: '/static/',
        filename: '[name].bundle.js',
        chunkFilename: '[name].bundle.js'
    },
    module: {
        loaders: [
            {
                test: /\.css$/,
                loader: 'style-loader!css'
            },
            {
                test: /\.less$/,
                loader: 'style-loader!css!less'
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: 'babel-loader',
                query: { stage: 0, optional: ['runtime'] }
            }
        ],
        noParse: [require.resolve('babel-core/browser.min')]
    },
    resolve: {
        extensions: ['', '.js'],
        modulesDirectories: ['node_modules'],
        alias: {
            'babel-transform': require.resolve('babel-core/browser.min')
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
            _: 'underscore',
            'es6-promise': 'es6-promise',
            'fetch': 'imports?this=>global!exports?global.fetch!whatwg-fetch'
        }),
        new webpack.DefinePlugin({
            'process.env': {
                NODE_ENV: JSON.stringify('production')
            }
        }),
        new webpack.optimize.CommonsChunkPlugin(
            'vendor', 'vendor.bundle.js', Infinity
        )
    ]
};

if (process.env.NODE_ENV === 'production') {
    config.plugins.push(
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
