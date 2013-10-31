class Context

	constructor: (@$timeout, @socket) ->
		@env = {}

	update: (key) ->
		console.log "context.update:", key, '->', @env[key] 

angular.module("app").service "context", ["$timeout", "socket", Context]
