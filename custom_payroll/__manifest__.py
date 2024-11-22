# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Custom HR Payroll',
    "version": "15.0.1.1.1",
    'category': 'Custom Payroll',
    'summary': 'Custom For Payroll',
    'description': """
       """,
    # 'website': '',
    'depends': [
        'hr',
        'om_hr_payroll',
    ],
    'images': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'wizard/update_amount_wizard.xml',
		'wizard/wizard_export_payslip.xml',
        'views/salary_correction.xml',
        'views/hr_salary_rule.xml',
        'views/premi.xml',
        'views/hr_contract.xml',
        'views/hr_payroll_structure.xml',
        'views/master_umk.xml',
        'views/hr_leave_type.xml',
        'views/hr_payslip.xml',
        'views/hr_job.xml',
		'views/menuitem.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'qweb': [
        # "static/src/xml/attendance.xml",
    ],
    'application': False,
}
