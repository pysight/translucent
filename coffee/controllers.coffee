AppController = ($scope, $timeout, $window, socket, context) ->

	socket.on "exception", -> window.location.reload true
	socket.on "connect", -> 
		console.log "on connect"
		socket.emit "env_init", $scope.env

	socket.on "send_value", (data) ->
		console.log "received value:", angular.toJson(data)
		$scope.$apply ->
			$scope.env[data.key] = data.value


	envWatcher = (e1, e2) -> _.each _.union(_.keys(e1), _.keys(e2)), (key) ->
		$timeout (-> context.update key), 0 unless _.isEqual e1[key], e2[key]
	$scope.$watch "env", envWatcher, true

	$scope.env = context.env

	socket.on "hello", (data) ->
		console.log "hello received"

angular.module("app").controller "AppController", 
	["$scope", "$timeout", "$window", "socket", "context", AppController]
