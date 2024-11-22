# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Custom HR',
    "version": "15.0.1.1.1",
    'category': 'Human Resources',
    'summary': 'Custom For Human Resources',
    'description': """
       """,
    # 'website': '',
    'depends': [
        'hr',
        'hr_attendance',
        'hr_skills',
        'hr_contract',
        'resource',
        'survey',

        'om_hr_payroll',
    ],
    'images': [
    ],
    'data': [
        'data/scheduled_action.xml',
        'data/data_employee_type.xml',
        'data/kompensasi_sequence.xml',
        'security/ir.model.access.csv',
        # 'security/rule.xml',
        'wizard/revise_wizard.xml',
        'report/report_pdm.xml',
        'report/report_terminasi.xml',
        'report/button_print.xml',
        'report/action_print.xml',
        'views/hr_attendance.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/work_location.xml',
        'views/inherit_hr_employee.xml',
        'views/hr_employee_grade.xml',
        'views/hr_employee_type.xml',
        'views/hr_resume.xml',
        'views/hr_kompensasi_pkwt.xml',
        'views/hr_promosi_demosi_mutasi.xml',
        'views/matrix_approval.xml',
        'views/form_lupa_absen.xml',
        'views/hr_terminasi.xml',
        'views/resource_calendar.xml',
        # paling bawah biar enjoy
        'views/menu_item.xml',
        
        # 'report/report_surat_teguran_template.xml',
        # 'report/report_surat_teguran.xml',
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
