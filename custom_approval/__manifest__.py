# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom approval',
    'version': '1.7',
    'category': 'approval',
    'author': 'DSI Bandung',
    'description': "Custom approval Module",
    'summary': 'Odoo 17 Custom approval Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'account',
        'sign',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'security/ir.model.access.csv',
        'views/level_of_approval.xml',
        'views/ir_menu.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
