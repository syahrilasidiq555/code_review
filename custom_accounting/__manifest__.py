# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom accounting',
    'version': '1.7',
    'category': 'accounting',
    'author': 'DSI Bandung',
    'description': "Custom accounting Module",
    'summary': 'Odoo 17 Custom accounting Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'sale',
        'account', 
        'account_accountant',
        'account_asset',
        'pdf_report_password_protection',
        'l10n_id_efaktur',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/account_asset.xml',
		'views/efaktur_views.xml',
        'reports/sisnet_invoice.xml',
        'reports/reports.xml',
        'reports/invoice.xml',
        'wizard/revaluasi_kurs.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
