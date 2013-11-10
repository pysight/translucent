app = angular.module "app"

class Socket

	constructor: (@$rootScope, @$timeout) ->
		@socket = io.connect "/api"
		@prefix = "socket:"

	wrap: (callback) ->
		(args...) => 
			f = -> callback.apply @socket, args
			@$timeout f, 0
			
	on: (e, callback) -> 
		@socket.on e, @wrap callback
	
	emit: (e, data, callback) ->
		if callback?
			@socket.emit e, data, @wrap callback
		else
			@socket.emit e, data

	unsubscribe: (args...) -> 
		@socket.removeListener.apply @socket, args

	forward: (events, scope) ->
		events = [events] unless angular.isArray events
		scope ?= @$rootScope
		_.each events, (e) ->
			f = @wrap (data) -> scope.$broadcast @prefix + e, data
			scope.$on "destroy", -> @socket.removeListener e, f
			@socket.on e, f

app.service "socket", ["$rootScope", "$timeout", Socket]
