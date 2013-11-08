angular.module("app").directive "trNav", ->
	restrict: "E"
	link: (scope, elem, attrs) ->
		elem = $(elem)
		nav_text_elem = elem.children ".tr-nav-text"
		scope.nav_items ?= []
		nav_id = "nav_item_" + scope.nav_items.length
		nav_text = nav_text_elem.html()
		scope.nav_items.push
			id: nav_id
			text: nav_text
		nav_text_elem.detach()
		elem.attr 'id', nav_id
