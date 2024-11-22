# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
import csv
import base64
import logging
import xlsxwriter

class dym_improvement_report_dep_wizard(models.TransientModel):
    _name = 'report.improvement.dep'
    _description = 'Improvement Report 2 Wizard' 

    department_ids = fields.Many2many('hr.department')
    
    start_date = fields.Date(string="Start Date", default=fields.Datetime.now, required=True)
    end_date = fields.Date(string="End Date", default=fields.Datetime.now,required=True)
    jenis_improvement = fields.Selection(
        [('qcc','QCC'),
        ('qcp','QCP'),
        ('qcl','QCL'),
        ('pps','PPS'),
        ('fiver','5R'),
        ('safety_improvement','Safety Improvement')],
        string='Jenis Improvement')
    

    
    def print_report(self):
        # raise exceptions.UserError(_('Disini'))
        department_ids = self.department_ids.ids
        start_date = self.start_date
        end_date = self.end_date
        jenis_improvement = self.jenis_improvement

        data = {
            'start_date': start_date,
            'end_date': end_date,
            'department_ids':department_ids,
            'jenis_improvement': jenis_improvement,
        }

        # _logger.info('DISINI TEST')
        # _logger.info('DATA '+str(data))

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('dym_improvement.report_improvement_dep_xlsx').report_action(self, data=data)