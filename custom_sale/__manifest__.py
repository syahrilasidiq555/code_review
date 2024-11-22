# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Sale',
    'version': '1.7',
    'category': 'Sale',
    'author': 'DSI Bandung',
    'description': "Custom Sale Module",
    'summary': 'Odoo 17 Custom Sale Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'sale_management', 
        'sign',
        'sale_subscription',
        'custom_approval',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/revise_wizard.xml',
        'wizard/sign_wizard.xml',
        'reports/sale_order.xml',
        'reports/sale_report.xml',
        'reports/report_sale_invoice.xml',
        'views/sale_order.xml',
        'views/portal_sale_order.xml',
        'views/sale_order_recurring.xml',

    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
