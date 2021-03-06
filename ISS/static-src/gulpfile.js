var gulp = require('gulp');
var flatten = require('gulp-flatten');
var less = require('gulp-sources-less');
var sourcemaps = require('gulp-sourcemaps');
var path = require('path');
var argv = require('yargs').argv;
var minifyCSS = require('gulp-minify-css');
var requirejsOptimize = require('gulp-requirejs-optimize');


var staticDir = '../static',
  jsDir = path.join(staticDir, 'js'),
  optimizeModules = [ 'thread.js' ];
 
gulp.task('less', function() {

  var lessStream = less({
      paths: [ path.join(__dirname, 'less') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  var stream = gulp.src('./src/**/*.less');

  stream = argv.optimize ? stream : stream.pipe(sourcemaps.init());
  stream = stream.pipe(lessStream);
  stream = argv.optimize ? stream : stream.pipe(sourcemaps.write());
  stream = stream.pipe(flatten());
  stream = argv.optimize ? stream.pipe(minifyCSS()) : stream;
  stream = stream.pipe(gulp.dest('../static/css'));

  return stream;
});

gulp.task('javascript', function() {
  return gulp.src('./src/**/*.js')
    .pipe(flatten())
    .pipe(gulp.dest(jsDir));
});

gulp.task('optimize-js', ['javascript'], function() {
  var optPaths = optimizeModules.map(function(moduleName) {
    return path.join(jsDir, moduleName);
  });

  return gulp.src(optPaths)
    .pipe(requirejsOptimize())
    .pipe(flatten())
    .pipe(gulp.dest('../static/js'));
});

var generateTasks = ['less']
generateTasks.push(argv.optimize ? 'optimize-js' : 'javascript');
gulp.task('generate', generateTasks);

gulp.task('watch', ['generate'], function() {
  gulp.watch([ './src/**/*.less' ], ['less']);
  gulp.watch([ './src/**/*.js' ], ['javascript']);
});
