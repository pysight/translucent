app = angular.module("app", [])

require "./socket.coffee"
require "./context.coffee"
require "./filters.coffee"
require "./directives.coffee"

AppController = ($scope, $timeout, socket, context) ->
	console.log socket
	socket.on "exception", ->
		window.location.reload true  # use $window?
	socket.on "connect", ->
		socket.emit "hello", {"a": "b"}
	socket.on "hello", (args) ->
		console.log "I GOT SOMETHING BACK"
	$scope.env = context.env
	envWatcher = (e1, e2) -> _.each _.union(_.keys(e1), _.keys(e2)), (key) ->
		$timeout (-> context.update key), 0 unless _.isEqual e1[key], e2[key]
	$scope.$watch "env", envWatcher, true
app.controller "AppController", ["$scope", "$timeout", "socket", "context", AppController]

angular.element(document).ready ->
	angular.bootstrap(document, ["app"])
