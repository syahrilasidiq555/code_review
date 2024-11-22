# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Web RDC',
    'version': '15.0.0',
    'category': 'RDC',
    'summary': "Module for RDC WEB",
    'author': 'DSI Bandung',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'website',
        'custom_sale_order',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_form_website.xml',
        'views/inherited_menu.xml',
        'views/res_hospital.xml',
        'reports/jenazah_report_view.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
