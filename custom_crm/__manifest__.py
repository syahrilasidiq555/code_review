# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom crm',
    'version': '1.7',
    'category': 'crm',
    'author': 'DSI Bandung',
    'description': "Custom crm Module",
    'summary': 'Odoo 17 Custom crm Module',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base', 
        'crm',
        'project_todo',
    ],
    'license': 'LGPL-3',
    'assets': {
    },
    'data': [
        'data/ir_cron.xml',
        'views/crm_lead.xml',
        'views/crm_stage.xml',
    ],
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
