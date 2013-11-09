AppController = ($scope, $timeout, $window, socket, context) ->
	socket.on "exception", -> $window.location.reload true
	$scope.env = context.env
	$scope.$watch "env", context.env_watcher, true

angular.module("app").controller "AppController", 
	["$scope", "$timeout", "$window", "socket", "context", AppController]
