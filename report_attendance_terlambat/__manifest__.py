# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Report Attendances Terlambat',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'sequence': 81,
    'summary': 'Report Attendance Summary and Employee',
    'description': """
    """,
    # 'website': '',
    'depends': [
        'hr',
        'barcodes',
        'report_xlsx',
        'hr_attendance',
        'custom_hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/report_attendance_dep_terlambat_view.xml',
        'wizard/report_attendance_emp_terlambat_view.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
