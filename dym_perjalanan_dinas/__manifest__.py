# -*- coding: utf-8 -*-

{
    'name': 'Perjalanan Dinas Karyawan',
    "version": "15.0.1.14.1",
    'category': 'Human Resources/Employees',
    'sequence': 75,
    'summary': 'Add menu Perjalanan Dinas Karyawan In Employee',
    'description': "Thiss module add new menu Perjalanan dinas Karyawan inside Employee Menu",
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'hr_holidays',
        'custom_hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/group_rule.xml',
        'views/perjalanan_dinas.xml',
        'report/button_print.xml',
        'report/perjalanan_dinas.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}