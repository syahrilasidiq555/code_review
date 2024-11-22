# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Purchase',
    'version': '15.0.0',
    'category': 'Purchase',
    'author': 'DSI Bandung',
    'description': "Custom Purchase for RDC",
    'summary': 'Odoo 15 Custom Purchase for RDC',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 'purchase', 'purchase_request', 
        'custom_accounting',
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_data.xml',
        'report/purchase_request.xml',
        'report/report.xml',
        'report/purchase_order.xml',
        'views/purchase_request.xml',
        'views/purchase_order.xml',
        'views/config_purchase_request.xml',
        'wizard/purchase_request_line_make_purchase_order_view.xml',
        'wizard/purchase_notify_vendor.xml',
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
