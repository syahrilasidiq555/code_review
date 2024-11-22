# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Cash Advance',
    'version': '15.0.0',
    'category': 'RDC',
    'summary': "Custom Cash Advance",
    'author': 'DSI Bandung',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'hr',
        'account_accountant',
        'custom_sale_order',
        'custom_accounting',
    ],
    'data': [
        # 'data/lang_data.xml',
        'security/ir.model.access.csv',
        'wizard/ca_realization_wizard.xml',
        'views/account_move.xml',
        'views/menu_item.xml',
        'views/cash_advance.xml',
    ],
    # 'assets': {
    #     # add di backend
    #     'web.assets_backend': [
    #         'rdc_module/static/src/scss/theme_color.scss',
    #     ],
    #     # add di frontend website
    #     'web.assets_common': [
    #         'rdc_module/static/src/scss/theme_color.scss',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
}
