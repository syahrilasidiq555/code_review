# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom POS',
    'version': '15.0.0',
    'category': 'POS',
    'author': 'DSI Bandung',
    'description': "Custom POS for RDC",
    'summary': 'Odoo 15 Custom POS for RDC',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 'point_of_sale', 'pos_sale', 'custom_sale_order'
    ],
    'license': 'LGPL-3',
    'data': [
        # 'security/ir.model.access.csv',
        'data/pos_payment_method.xml',
        'views/pos_order_view.xml',
        'views/account_move.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'custom_pos/static/src/js/db.js',
            'custom_pos/static/src/js/models.js',
            'custom_pos/static/src/js/ClientListScreen.js',
        ],
        'web.assets_qweb': [
            'custom_pos/static/src/xml/ClientLine.xml',
            'custom_pos/static/src/xml/ClientListScreen.xml',
            'custom_pos/static/src/xml/SaleOrderList.xml',
            'custom_pos/static/src/xml/ProductInfoPopup.xml',
            'custom_pos/static/src/xml/OrderReceipt.xml',
            'custom_pos/static/src/xml/PaymentScreenStatus.xml',
        ],
    },
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
