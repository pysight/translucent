import gulp from 'gulp';
import cssmin from 'gulp-cssmin';
import concat from 'gulp-concat';
import debug from 'gulp-debug';
import less from 'gulp-less';
import plumber from 'gulp-plumber';
import rename from 'gulp-rename';
import uglify from 'gulp-uglify';
import gutil from 'gulp-util';
import path from 'path';
import webpack from 'webpack';

import webpackConfig from './webpack.config.babel';

const STATIC = path.join(__dirname, 'translucent/static');
const PRODUCTION = process.env.NODE_ENV === 'production';
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
    return gulp.src(
        [
            `${NPM}/bootstrap/dist/css/bootstrap.min.css`,
            `${NPM}/font-awesome/css/font-awesome.min.css`
        ])
        .pipe(debug({title: 'vendor:css'}))
        .pipe(concat('vendor.min.css'))
        .pipe(PRODUCTION ? cssmin() : gutil.noop())
        .pipe(gulp.dest(STATIC));
});

gulp.task('vendor:babel', () => {
    return gulp.src(`${NPM}/babel-core/browser.min.js`)
        .pipe(debug({title: 'babel-transform.js'}))
        .pipe(PRODUCTION ? uglify() : gutil.noop())
        .pipe(rename('babel-transform.js'))
        .pipe(gulp.dest(STATIC));
});

gulp.task('vendor', ['vendor:css', 'vendor:fonts', 'vendor:babel']);
gulp.task('webpack', callback => {
    function onError(error, stats) {
        if (error) {
            return callback(new gutil.PluginError('webpack', error));
        } else {
            gutil.log('[webpack]', stats.toString());
            return callback();
        }
    }
    webpack(webpackConfig, onError);
});

gulp.task('build', ['webpack', 'vendor', 'less']);
gulp.task('dev', ['webpack', 'less']);

gulp.task('watch', ['dev'], () => {
    gulp.watch(['js/*.js', 'less/*.less'], ['dev']);
});

gulp.task('default', ['build']);
