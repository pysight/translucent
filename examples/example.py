# -*- coding: utf-8 -*-

from translucent import Server, App, BootstrapUI

ui = BootstrapUI('bootstrap-sidebar', 'My App')
ui.set('top')(
    ui.header('Title', 'Subtitle')['Header text.']
)
ui.set('left')(
    ui.navlist,
    ui.hr,
    ui.select('style', ['default', 'success', 'info', 'warning', 'danger'], init='default')
)
ui.set('right')(
    ui.panel('A panel', style='env.style')[
        ui.p[
            ui.list('unordered', nav='Menu Item #1')(
                'item1', 'item2', 'item3', 'item4'),
            ui.list('ordered', data='x in [1, 2, 3, 4]', nav='Menu Item #2')(
                'item{{x}}')
        ]
    ]
)
Server(App(), ui, host='0.0.0.0', port=5000).run()
