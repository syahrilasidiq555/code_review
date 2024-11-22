# -*- coding: utf-8 -*-

{
    'name': 'Custom HR Recruitment',
    "version": "15.0.1.1.1",
    'sequence': 75,
    'summary': 'Custom HR Recruitment',
    'description': "",
    'depends': [
        'base',
        'hr',
        'web',
        'website',
        'custom_hr',
        'hr_recruitment',
        'website_hr_recruitment',
    ],
    'images': [
    ],
    'data': [
        # 'data/mail_template.xml',
        # 'data/scheduled_action.xml',
        'data/mail_templates.xml',
        'data/default_data.xml',
        'security/group_rule.xml',
        'security/ir.model.access.csv',

        'report/report_fpk.xml',
        'report/action_print.xml',

        'views/big_fpk.xml',
        'views/big_fpk_matrix_approval.xml',
        'views/website_hr_recruitment_templates.xml',
        'views/hr_applicant.xml',
        'views/hr_job.xml',
    ],
    'assets': {
        # add di backend
        'web.assets_frontend': [
            'custom_hr_recruitment/static/js/hr_applicant.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}