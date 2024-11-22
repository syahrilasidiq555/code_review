# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BIG Module',
    'version': '15.0.0',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'license': 'LGPL-3',
    'depends': [
        'base',

        'mail',
        'contacts',
        'calendar',
        'website',
        'website_slides',
        'survey',
        'hr',
        'hr_holidays',
        'hr_attendance',
        'hr_contract',
        'hr_recruitment',
        'hr_skills',
        'website_hr_recruitment',

        # app.odoo.com module
        'ks_binary_file_preview',
        'report_pdf_options',
        'report_xlsx',
        'web_domain_field',
        'web_drop_target',
        'web_responsive',
        # 'list_view_sticky_header',
        'om_hr_payroll',
        'mail_preview_base',
        'base_user_role',
        'dms',
        # 'hr_dms_field',
        'hr_organizational_chart',
        'web_widget_image_webcam',
        'odoo_attendance_user_location',
        
        
        # custom module
        'custom_hr',
        'suggestion_system',
        'dym_improvement',
        'dym_performance_appraisal',
        'report_attendance_terlambat',
        'report_survey',
        'custom_hr_recruitment',
        'custom_finger_attendance',
        'custom_payroll',

    ],
    'data': [
        'data/lang_data.xml',
    ],
    # 'assets': {
    #     # add di backend
    #     'web.assets_backend': [
    #         'big_module/static/src/scss/custom.scss',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
}
