# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Inventory',
    'version': '15.0.0',
    'category': 'Inventory',
    'author': 'DSI Bandung',
    'description': "Custom Inventory for RDC",
    'summary': 'Odoo 15 Custom Inventory for RDC',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 'product', 'stock', 'stock_account', 'sale_stock'
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/product.xml',
        'views/stock_picking.xml',
        'views/stock_move.xml',
        'views/stock_move_line.xml',
        'views/res_users.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
        # 'web.assets_backend': [
        #     'custom_sale_order/static/src/scss/custom.scss',
        #     'custom_sale_order/static/src/js/qty_at_date_widget.js',
        # ],
        # 'web.assets_qweb': [
        #     'custom_sale_order/static/src/xml/**/*',
        # ],
    },
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
