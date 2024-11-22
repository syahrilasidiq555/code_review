# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Manufacturing',
    'version': '1.7',
    'category': 'Manufacturing',
    'author': 'DSI Bandung',
    'description': "Custom Manufacturing Module",
    'summary': 'Odoo 17 Custom Manufacturing Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'mrp',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'views/mrp_production_views.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
