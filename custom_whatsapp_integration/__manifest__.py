# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Whatsapp Integration RDC',
    'version': '15.0.0',
    'category': 'RDC',
    'summary': "Module for RDC WEB",
    'author': 'DSI Bandung',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'purchase',
        'crm',
        'custom_sale_order',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/whatsapp_credentials.xml',
        'views/purchase.xml',
        'views/whatsapp_credentials.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
