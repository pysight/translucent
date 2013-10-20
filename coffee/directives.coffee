angular.module("app").directive "trNav", ->
	(scope, elem, attrs) ->
		console.log attrs
		scope.nav_items ?= []
		scope.nav_items.push
			id: "nav_item_" + scope.nav_items.length
			text: attrs.trNav
