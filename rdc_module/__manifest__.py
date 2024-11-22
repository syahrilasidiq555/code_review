# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'RDC Module',
    'version': '15.0.0',
    'category': 'RDC',
    'summary': "Module for RDC",
    'author': 'DSI Bandung',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        
        'sale_management',
        'account',
        'crm',
        'website',
        'stock',
        'account_accountant',
        'purchase',
        # 'point_of_sale',
        'mail',
        'contacts',
        'sale_renting',

        # app.odoo.com module
        'sale_order_line_multi_warehouse',
        'report_qweb_element_page_visibility',
        'report_pdf_options',
        'web_domain_field',
        'bi_pos_warehouse_management',
        'ks_binary_file_preview',
        'auth_session_timeout',
        'auditlog',
        
        # our customized module
        'custom_sale_order',
        'custom_web_rdc',
        'custom_accounting',
        'custom_opening_asset',
        'custom_inventory',
        'custom_purchase',
        'custom_pos',
        'custom_crm',
        # 'custom_cash_advance',

        # place in the bottom
        'custom_whatsapp_integration',
        'custom_access_right',

    ],
    'data': [
        'data/lang_data.xml',
    ],
    'assets': {
        # add di backend
        'web.assets_backend': [
            'rdc_module/static/src/js/basic_fields.js',
            'rdc_module/static/src/scss/theme_color.scss',
        ],
        # add di frontend website
        'web.assets_common': [
            'rdc_module/static/src/js/utils.js',
            'rdc_module/static/src/js/auto.js',
            'rdc_module/static/src/scss/theme_color.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
