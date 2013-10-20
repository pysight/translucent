class Context

	constructor: (@$timeout, @socket) ->
		@env = {}

angular.module("app").service "context", ["$timeout", "socket", Context]