angular.module("app").filter "sprintf", -> 
	(value, format) -> _.str.sprintf format, value

angular.module("app").filter "map", ->
	(value, mapping) -> mapping[value] ? mapping['?']
