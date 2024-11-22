# -*- coding: utf-8 -*-

{
    'name': 'Improvement',
    "version": "15.0.1.1.1",
    'category': 'Improvement',
    'sequence': 75,
    'summary': 'Insert QCC, QCP, QCL, PPS, 5R, Safety Improvement',
    'description': "",
    'depends': [
        'base',
        'hr',
        'suggestion_system',
        'web_domain_field',
        'report_xlsx',
    ],
    'images': [
        'static/description/icon.png'
    ],
    'data': [
        # 'data/mail_template.xml',
        # 'data/scheduled_action.xml',
        'wizard/revise_wizard.xml',
        'wizard/report_improvement_view.xml',
        'wizard/report_improvement_tahunan_view.xml',
        'wizard/report_improvement_2_view.xml',
        'views/dym_improvement_view.xml',
        'views/dym_improvement_line_view.xml',
        'views/improvement_step_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}