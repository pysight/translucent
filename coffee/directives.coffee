angular.module("app").directive "trNav", ->
	restrict: "E"
	link: (scope, elem, attrs) ->
		nav_text = $(elem).children ".tr-nav-text"
		scope.nav_items ?= []
		scope.nav_items.push
			id: "nav_item_" + scope.nav_items.length
			text: nav_text.html()
		nav_text.detach()
