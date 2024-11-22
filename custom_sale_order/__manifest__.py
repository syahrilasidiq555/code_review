# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Sale Order',
    'version': '15.0.0',
    'category': 'Sale Order',
    'author': 'DSI Bandung',
    'description': "Custom Sale Order for RDC",
    'summary': 'Odoo 15 Custom Sale Order for RDC',
    'website': 'https://www.sample.com',
    'email': 'sample@sample.com',
    'depends': [
        'base',
        'hr',
        'sale',
        'purchase',
        'stock',
        'sale_stock',
        'sale_renting',
        'sale_order_line_multi_warehouse',
        'web_domain_field',
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/product_category.xml',
        'data/ruangdoa_jadwal.xml',
        'data/product_product.xml',
        'data/decimal_precision.xml',
        'data/pendapatan_columbarium_data.xml',
        'data/ir_cron.xml',
        'wizard/view_bundle_wizard.xml',
        'wizard/confirm_wizard_view.xml',
        'wizard/choose_partner_wizard.xml',
        'wizard/change_product_wizard.xml',
        'wizard/add_ruang_semayam_wizard.xml',
        'wizard/add_transportasi_wizard.xml',
        'wizard/add_columbarium_wizard.xml',
        'wizard/add_ruangdoa_wizard.xml',
        'wizard/add_larung_wizard.xml',
        'views/view_product_template.xml',
        'views/view_bundle_product.xml',
        'views/view_sale_order.xml',
        'views/cost_sheet_view.xml',
        'views/view_purchase_order.xml',
        'views/views_res_partner.xml',
        'views/rental_schedule_view.xml',
        'views/res_config_settings.xml',
        'views/account_move_views.xml',
        'views/parking_voucher.xml',
        'views/master_tarif_ambulance.xml',
        'views/product_product.xml',
        'views/jadwal_ruangdoa.xml',
        'views/res_pemakaman.xml',
        'report/report_sale_order_document.xml',
        'report/report_template.xml',
        'report/parking_voucher_printout.xml',
        'report/sale_order_printout.xml',
        'report/invoice.xml',
        'report/bon_pemesanan_vendor.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_sale_order/static/src/scss/custom.scss',
            'custom_sale_order/static/src/js/qty_at_date_widget.js',
        ],
        'web.assets_qweb': [
            'custom_sale_order/static/src/xml/**/*',
        ],
    },
    "images": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
