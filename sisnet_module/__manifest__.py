# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'SISNET Module',
    'version': '1.7',
    'category': 'SISNET',
    'summary': "Module for SISNET",
    'author': 'PT. Dwidasa Samsara Indonesia',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        
        'sale_management',
        'account_accountant',
        'crm',
        'website',
        'stock',
        'purchase',
        'project',
        'mrp',
        'web_studio',
        'documents',
        'hr',
        'sale_subscription',
        'sign',
        'contacts',
        'calendar',
        'stock_barcode',
    
        # downlodable module
        'purchase_request',
        'pdf_report_password_protection',

        # customable module
        'custom_approval',
        'custom_contact',
        'custom_crm',
        'custom_sale',
        'custom_accounting',
        'custom_purchase_inventory',
        'custom_mrp',
        'custom_project',

    ],
    'data': [
        'data/lang_data.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False,
}
