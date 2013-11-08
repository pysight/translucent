angular.module("app").filter "sprintf", ->
	(format, args...) -> _.str.sprintf format, args...

angular.module("app").filter "map", ->
	(value, mapping) -> mapping[value] ? mapping['?']
