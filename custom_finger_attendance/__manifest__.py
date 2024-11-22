# -*- coding: utf-8 -*-

{
    'name': 'Finger Attendance',
    "version": "15.0.1.1.1",
    'sequence': 75,
    'summary': 'Finger Attendance',
    'description': "",
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'custom_hr',
    ],
    'images': [
    ],
    
    'data': [
        # 'data/mail_template.xml',
        'data/ir_cron.xml',
        # 'data/scheduled_action.xml',
        'security/ir.model.access.csv',
        'wizard/generate_attendance_wizard.xml',
        # 'security/group_rule.xml',
        'views/finger_attendance.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}