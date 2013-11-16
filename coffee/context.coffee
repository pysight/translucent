app = angular.module "app"

class Context

    constructor: (@$timeout, @$rootScope, @$log, @socket) ->
        @env = {}
        @out = {}
        @readonly = {}
        @socket.on "value_update", @on_value_update
        @socket.on "output_update", @on_output_update
        @socket.on "connect", @on_connect

    update: (key) =>
        @$log.log 'context.update():', key, '->', @env[key]
        if not @readonly[key]
            @$log.log "\tsocket.emit('input_update'):", key, '->', @env[key]
            @socket.emit "input_update",
                key: key
                value: @env[key]

    env_watcher: (e1, e2) =>
        _.each _.union(_.keys(e1), _.keys(e2)), (key) =>
            if not _.isEqual e1[key], e2[key]
                @$timeout (=> @update key), 0

    on_value_update: (data) =>
        @$log.log "context.on_value_update(): ", angular.toJson(data)
        @readonly[data.key] = data.readonly
        @$rootScope.$apply =>
            @env[data.key] = data.value

    on_output_update: (data) =>
        @$log.log "context.on_output_update(): ", angular.toJson(data)
        @$rootScope.$apply =>
            @out[data.key] = {"data": {}}
            for k, v of data.data
                @out[data.key].data[k] = v

    on_connect: =>
        @$log.log "context.on_connect()"
        env = {}
        for k, v of @env
            if not @readonly[k]?
                env[k] = v
        @$log.log "\tsocket.emit('inputs_init'):", angular.toJson(env)
        @socket.emit "inputs_init", env

app.service "context", ["$timeout", "$rootScope", "$log", "socket", Context]
