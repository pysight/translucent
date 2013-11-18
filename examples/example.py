# -*- coding: utf-8 -*-

from translucent import Server, App, BootstrapUI

ui = BootstrapUI('bootstrap-sidebar', 'My App')

ui.set('top')(ui.header('Translucent', 'UI Demo')[
    'Lorem ipsum dolor sit amet, consectetur adipisicing.'])

ui.set('left')(ui.navlist)

spinner = ui.icon('fa-spinner', spin=True, fixed=True)

ui.set('right')(
    ui.h4(nav=[spinner, 'Panel'])[spinner, 'Panel'],
    ui.panel('Reactive Test', style='primary')[
        ui.select('object', "obj.id as obj.name for obj in env.objects",
            label='Select an object:'),
        ui.p['Selected object: {{ env.object }}']
    ],
    ui.panel('Panel (style: {{ env.style }})', style='env.style', title='env.title')[
        ui.p['Lorem ipsum dolor sit amet, consectetur adipisicing elit. Perspiciatis, modi!'],
        ui.panel[
            ui.select('style', ['default', 'primary', 'success', 'info', 'warning', 'danger'],
                label='Choose heading style', init='primary'),
            ui.checkbox('title', 'Large title', init=False)
        ]
    ],
    ui.panel('Select values are not passed as strings!', style='primary')[
        ui.select('a', [1, 2, 3], label='a', init=1),
        ui.select('b', [4, 5, 6], label='b', init=4),
        '{{ env.a }} + {{ env.b }} = {{ env.a + env.b }}'
    ]
)


class ExampleApp(App):

    @classmethod
    def on_start(cls):
        cls.objects = [
            {'id': 0, 'name': 'Foo'},
            {'id': 1, 'name': 'Bar'},
            {'id': 2, 'name': 'Baz'}
        ]

    def on_init(self):
        self.set_value('objects', self.objects, shared=True)
        self.set_input('object', 0)

Server(ExampleApp, ui, host='0.0.0.0', port=5000).run()
