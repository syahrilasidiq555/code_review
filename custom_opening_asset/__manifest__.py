# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Opening Asset',
    'version': '15.0.0',
    'category': 'Accounting',
    'author': 'Rajib Deyana, Henrawan Muhlisin, DSI Bandung',
    'summary': "Odoo 15 Custom Asset Management.",
    'website': 'https://www.dwidasa.com',
    'email': 'community@dwidasa.com',
    'depends': ['account', 'account_asset'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/account_asset_action.xml',
        'views/account_asset_views.xml',
        'views/account_asset_correction_views.xml',
        'views/account_move_views.xml',        
        'views/res_config_settings_views.xml',
        'wizard/account_asset_validate_confirm_views.xml',
        'views/account_deffered_revenue.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
