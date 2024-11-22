# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
import csv
import base64
import logging
import xlsxwriter
from datetime import timezone, datetime, timedelta

class report_performance_belum_employee_wizard(models.TransientModel):
    _name = 'report.performance.belum.employee.wizard'
    _description = 'Report Performance Belum Isi to Employee Answered Wizard' 

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", default=datetime.now()+timedelta(hours=7), required=True)
    department_ids = fields.Many2many('hr.department')
    tipe_report = fields.Selection([('form_a','Form A'),('form_b','Form B')],'Tipe Report',required=True)
    periode = fields.Selection([(str(num), str(num)) for num in range(2020, ((datetime.now().year)+1) )], 'Periode',required=True)

    def print_report(self):
        start_date = self.start_date
        end_date = self.end_date
        department_ids = self.department_ids.ids
        tipe_report = self.tipe_report
        periode = self.periode

        data = {
            'start_date': start_date,
            'end_date': end_date,
            'department_ids': department_ids,
            'tipe_report':tipe_report,
            'periode':periode
        }

        return self.env.ref('dym_performance_appraisal.report_performance_belum_employee').report_action(self, data=data)