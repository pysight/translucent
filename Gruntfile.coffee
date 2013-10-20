module.exports = (grunt) ->

	grunt.initConfig
		pkg: grunt.file.readJSON 'package.json'
		watch:
			coffee:
				files: ['coffee/*.coffee']
				tasks: ['coffee-task']
				options:
					interrupt: yes
			stylus:
				files: ['stylus/*.styl']
				tasks: ['stylus-task']
				options:
					interrupt: yes
		useminPrepare:
			html: ['templates/vendor.html']
		copy:
			vendor:
				files: [
					{expand: true, cwd: 'bower_components/chosen', src: '*.png', dest: 'static/vendor/'}
				]
		coffeeify:
			options:
				debug: true 
			files:
				src: ['coffee/*.coffee']
				dest: 'static/js/app.js'
		stylus:
			compile:
				files:
					'static/css/style.css': 'stylus/*.styl'

	grunt.loadNpmTasks('grunt-contrib-copy')
	grunt.loadNpmTasks('grunt-contrib-watch')
	grunt.loadNpmTasks('grunt-contrib-stylus')
	grunt.loadNpmTasks('grunt-contrib-cssmin')
	grunt.loadNpmTasks('grunt-contrib-concat')
	grunt.loadNpmTasks('grunt-contrib-uglify')
	grunt.loadNpmTasks('grunt-coffeeify')
	grunt.loadNpmTasks('grunt-usemin')

	grunt.registerTask 'coffee-task', ['coffeeify']
	grunt.registerTask 'stylus-task', ['stylus']

	grunt.registerTask 'dist', ['copy:vendor', 'useminPrepare', 'concat', 'cssmin', 'uglify']
	grunt.registerTask 'build', ['coffeeify', 'stylus']
	grunt.registerTask 'default', ['build']
	grunt.registerTask 'dev', ['build', 'watch']
	grunt.registerTask 'all', ['dist', 'build']
