app = angular.module("app", [])

require "./socket.coffee"
require "./context.coffee"
require "./filters.coffee"
require "./directives.coffee"

AppController = ($scope, socket) ->
	console.log socket
	socket.on "exception", ->
		window.location.reload true  # use $window?
	socket.on "connect", ->
		socket.emit "hello", {"a": "b"}
	socket.on "hello", (args) ->
		console.log "I GOT SOMETHING BACK"
app.controller "AppController", ["$scope", "socket", AppController]

angular.element(document).ready ->
	angular.bootstrap(document, ["app"])
