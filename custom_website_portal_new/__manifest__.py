# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Website Portal New',
    'version': '15.0.1',
    'category': 'Website',
    'author': 'DSI Bandung',
    'summary': "Odoo 15 Custom Website Portal",
    'website': 'https://www.dwidasa.com',
    'email': 'community@dwidasa.com',
    'depends': [
        'web',
        'custom_website_portal',
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # 'data/web_menu.xml',
    ],
    'assets': {
        # 'web.assets_frontend': [
        #     'custom_website_portal/static/src/scss/extra.scss',
        #     'custom_website_portal/static/src/js/form_views.js',
        #     'custom_website_portal/static/src/js/list_views.js',
        #     'custom_website_portal/static/src/scss/dependencies.scss',
        #     'custom_website_portal/static/src/scss/en_home_menu.scss',
        #     'custom_website_portal/static/src/scss/en_home_menu_layout.scss',
        # ],
        # 'web.assets_common': [
        #     'custom_website_portal/static/src/scss/dependencies.scss',
        #     'custom_website_portal/static/src/scss/en_home_menu.scss',
        #     'custom_website_portal/static/src/scss/en_home_menu_layout.scss',
        # ],
    },
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}