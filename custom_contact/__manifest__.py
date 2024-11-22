# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Contact',
    'version': '1.7',
    'category': 'Contact',
    'author': 'DSI Bandung',
    'description': "Custom Contact Module",
    'summary': 'Odoo 17 Custom Contact Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'contacts', 
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/segment.xml',
        'views/menuitem.xml',
        'wizard/partner_customer_id.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
