# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Purchase Inventory',
    'version': '1.7',
    'category': 'Purcahse Inventory',
    'author': 'DSI Bandung',
    'description': "Custom Purcahse Inventory Module",
    'summary': 'Odoo 17 Custom Purcahse Inventory Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'stock',
        'project',
        'purchase',
        'repair',
        'purchase_stock',

        # downloaded module
        'purchase_request',
        
        # custom module
        'custom_approval',
        'custom_sale',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_default.xml',
        'data/operation_type.xml',
        'security/ir_rule.xml',
        'views/stock_warehouse.xml',
        'views/purchase_request.xml',
        'views/purchase.xml',
        'views/res_users.xml',
        'views/stock_picking.xml',
        'views/repair_order.xml',
        'views/report_purchase.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
