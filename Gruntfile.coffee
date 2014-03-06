module.exports = (grunt) ->

	require('load-grunt-tasks')(grunt)

	grunt.initConfig
		pkg: grunt.file.readJSON "package.json"
		watch:
			coffee:
				files: ["coffee/*.coffee"]
				tasks: ["coffee-task"]
				options:
					interrupt: yes
			stylus:
				files: ["stylus/*.styl"]
				tasks: ["stylus-task"]
				options:
					interrupt: yes
		useminPrepare:
			html: ["templates/vendor.html"]
		copy:
			vendor:
				files: [
					{
						expand: true, 
						cwd: "bower_components/chosen/public", 
						src: "*.png", 
						dest: "static/vendor"
					},
					{
						expand: true,
						cwd: "bower_components/font-awesome/fonts",
						src: "*.*",
						dest: "static/fonts"
					},
					{
						expand: true,
						cwd: "bower_components/angular-chosen-localytics",
						src: "*.gif",
						dest: "static/vendor"
					}
				]
		coffeelint:
			app: ["coffee/*.coffee"]
			options:
				indentation:
					value: 4
		browserify:
  			dist:
    			files:
      				"static/js/app.js": ["coffee/*.coffee"]
    		options:
      			transform: ["coffeeify"]
      			debug: true
		stylus:
			compile:
				files:
					"static/css/style.css": "stylus/*.styl"
		coffee:
			chosen:
				files: {
					"bower_components/chosen/public/chosen.jquery.js": [
						"bower_components/chosen/coffee/lib/select-parser.coffee",
						"bower_components/chosen/coffee/lib/abstract-chosen.coffee",
						"bower_components/chosen/coffee/chosen.jquery.coffee"
					]
				}
		compass:
			chosen:
				options:
					basePath: "bower_components/chosen"
					sassDir: "sass"
					cssDir: "public"
		less:
			chosen:
				files: {
					"bower_components/chosen-bootstrap/chosen-bootstrap.css":
						"bower_components/chosen-bootstrap/build.less"
				}
		less_imports:
			"bower_components/chosen-bootstrap/build.less": [
				"bower_components/bootstrap/less/variables.less",
				"bower_components/bootstrap/less/mixins.less",
				"bower_components/chosen-bootstrap/bootstrap-chosen.less"
			]

	grunt.registerTask "chosen", ["coffee:chosen", "compass:chosen", 
		"less_imports", "less:chosen"]
	grunt.registerTask "dist", ["chosen", "copy:vendor", 
		"useminPrepare", "concat", "cssmin", "uglify"]
	grunt.registerTask "build", ["browserify", "coffeelint", "stylus"]
	grunt.registerTask "default", ["build"]
	grunt.registerTask "dev", ["build", "watch"]
	grunt.registerTask "all", ["dist", "build"]
