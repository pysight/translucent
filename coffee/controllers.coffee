app = angular.module "app"

AppController = ($scope, $timeout, $window, socket, context) ->
    socket.on "exception", -> $window.location.reload true
    $scope.env = context.env
    $scope.$watch "env", context.env_watcher, true

app.controller "AppController",
    ["$scope", "$timeout", "$window", "socket", "context", AppController]
