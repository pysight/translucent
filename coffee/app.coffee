app = angular.module "app", []

require "./socket.coffee"
require "./context.coffee"
require "./filters.coffee"
require "./directives.coffee"
require "./controllers.coffee"

app.config ($logProvider) -> $logProvider.debugEnabled true
angular.element(document).ready -> angular.bootstrap document, ["app"]
