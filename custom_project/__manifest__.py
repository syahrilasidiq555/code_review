# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Project',
    'version': '1.7',
    'category': 'Project',
    'author': 'DSI Bandung',
    'description': "Custom Project Module",
    'summary': 'Odoo 17 Custom Project Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'custom_purchase_inventory',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'data/project_sequence.xml',
        'views/project_project_views.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
