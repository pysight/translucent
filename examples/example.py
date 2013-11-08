# -*- coding: utf-8 -*-

from translucent import Server, App, BootstrapUI

ui = BootstrapUI('bootstrap-sidebar', 'My App')

ui.set('top')(ui.header('Translucent', 'UI Demo')[
    'Lorem ipsum dolor sit amet, consectetur adipisicing.'])

ui.set('left')(ui.navlist)

spinner = ui.icon('fa-spinner', spin=True, fixed=True)

ui.set('right')(

    ui.h4(nav=ui.merge(spinner, 'Panel'))[spinner, 'Panel'],
    ui.panel('Panel title', style='env.style', title='env.title')[
        'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Perspiciatis, modi!'
    ],
    ui.panel[
        ui.select('style', ['default', 'primary', 'success', 'info', 'warning', 'danger'],
            label='Heading style', init='primary'),
        ui.checkbox('title', 'Large title', init=False)
    ],
)

Server(App(), ui, host='0.0.0.0', port=5000).run()
