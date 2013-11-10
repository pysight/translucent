app = angular.module "app"

app.filter "sprintf", ->
	(format, args...) -> _.str.sprintf format, args...

app.filter "map", ->
	(value, mapping) -> mapping[value] ? mapping['?']

app.filter "unsafe", ($sce) ->
	(value) -> $sce.trustAsHtml value
