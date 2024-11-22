# -*- coding: utf-8 -*-

{
    'name': 'Overtime Management',
    "version": "15.0.1.1.1",
    'sequence': 75,
    'summary': 'Overtime Management',
    'description': "",
    'depends': [
        'base',
        'hr',
        'custom_hr',
        'om_hr_payroll',
    ],
    'images': [
        'static/description/icon.png'
    ],
    
    'data': [
        # 'data/mail_template.xml',
        # 'data/scheduled_action.xml',
        'security/ir.model.access.csv',
        'security/group_rule.xml',
        'views/big_overtime.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}