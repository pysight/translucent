import gulp from 'gulp';
import cssmin from 'gulp-cssmin';
import concat from 'gulp-concat';
import debug from 'gulp-debug';
import less from 'gulp-less';
import plumber from 'gulp-plumber';
import gutil from 'gulp-util';
import path from 'path';
import webpack from 'webpack';

import webpackConfig from './webpack.config.babel';

const STATIC = path.join(__dirname, 'translucent/static');
const NPM = path.join(__dirname, 'node_modules');

gulp.task('vendor:fonts', () => {
    return gulp.src(`${NPM}/font-awesome/fonts/*.*`)
        .pipe(gulp.dest(`${STATIC}/fonts`));
});

gulp.task('less', () => {
    return gulp.src('less/*.less')
        .pipe(plumber({ errorHandler: err => console.error(err.toString()) }))
        .pipe(less())
        .pipe(concat('style.css'))
        .pipe(gulp.dest(STATIC));
});

gulp.task('vendor:css', () => {
    return gulp.src([
            `${NPM}/bootstrap/dist/css/bootstrap.min.css`,
            `${NPM}/font-awesome/css/font-awesome.min.css`
        ])
        .pipe(debug({title: 'vendor:css'}))
        .pipe(concat('vendor.min.css'))
        .pipe(cssmin())
        .pipe(gulp.dest(STATIC));
});

gulp.task('vendor', ['vendor:css', 'vendor:fonts']);
gulp.task('webpack', callback => {
    function onError(error, stats) {
        if (error) {
            callback(new gutil.PluginError('webpack', error));
        } else {
            gutil.log('[webpack]', stats.toString());
            callback();
        }
    }
    webpack(webpackConfig, onError);
});

gulp.task('build', ['webpack', 'vendor', 'less']);
gulp.task('dev', ['webpack', 'less'])

gulp.task('watch', ['dev'], () => {
    gulp.watch(['js/*.js', 'less/*.less'], ['dev'])
});

gulp.task('default', ['build']);
