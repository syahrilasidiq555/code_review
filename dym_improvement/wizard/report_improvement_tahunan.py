# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta

from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
import csv
import base64
import logging
import xlsxwriter

STATE_SELECTION = [
        ('new', 'New'),
        ('rfa','Request For Approval'),
        ('in_progress', 'In Progress'),
        ('approved', 'PIC SS Approved'),
        ('refuse', 'Refused'),
        ('revise','Revised'),
        ('done', 'Done')
    ]

    
class dym_improvement_report_tahunan_wizard(models.TransientModel):
    _name = 'report.improvement.tahunan'
    _description = 'Improvement Report tahunan' 

    def _default_get_this_year(self):
        date_now = datetime.now().date()
        year_now = str(date_now.year)
        return year_now

    department_ids = fields.Many2many('hr.department')
    state = fields.Selection(selection=STATE_SELECTION, string='State')
    tahun = fields.Selection([
        ('2020','2020'),
        ('2021','2021'),
        ('2022','2022'),
        ('2023','2023'),
        ('2024','2024'),
        ('2025','2025'),
        ('2026','2026')
    ] ,string='Tahun', required=True, default=_default_get_this_year)
    jenis_improvement = fields.Selection(
        [('qcc','QCC'),
        ('qcp','QCP'),
        ('qcl','QCL'),
        ('pps','PPS'),
        ('fiver','5R'),
        ('safety_improvement','Safety Improvement')],
        string='Jenis Improvement')
    level = fields.Selection(
        [('bronze','BRONZE'),
        ('silver','SILVER'),
        ('gold','GOLD')],
        string='Level')
    
    
    def print_report(self):
        # raise exceptions.UserError(_('Disini'))
        department_ids = self.department_ids.ids
        state = self.state
        tahun = self.tahun
        level = self.level
        jenis_improvement = self.jenis_improvement
        

        data = {
            'state': state,
            'tahun': tahun,
            'level': level,
            'jenis_improvement':jenis_improvement,
            'department_ids':department_ids,
        }

        # _logger.info('DISINI TEST')
        # _logger.info('DATA '+str(data))

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('dym_improvement.report_improvement_tahunan_xlsx').report_action(self, data=data)