# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Custom Meeting Booth',
    "version": "15.0.1.1.1",
    'category': 'Meeting Booth',
    'summary': 'Meeting Booth',
    'description': """
       """,
    # 'website': '',
    'depends': [
        'base',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/master_meeting_booth.xml',
        'views/meeting_booth.xml',
        'views/menu_item.xml',
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
