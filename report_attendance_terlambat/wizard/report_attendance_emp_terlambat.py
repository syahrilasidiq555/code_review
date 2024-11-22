# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
import csv
import base64
import logging
import xlsxwriter

class report_attendance_emp_terlambat(models.TransientModel):
    _name = 'report.attendance.emp.terlambat'
    _description = 'Attendance Department (Terlambat)' 

    department_ids = fields.Many2many('hr.department')
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", default=fields.Datetime.now,required=True)

    def print_report(self):
        # raise exceptions.UserError(_('Disini'))
        department_ids = self.department_ids.ids
        start_date = self.start_date
        end_date = self.end_date


        data = {
            'start_date': start_date,
            'end_date': end_date,
            'department_ids':department_ids,
        }

        # _logger.info('DISINI TEST')
        # _logger.info('DATA '+str(data))

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('report_attendance_terlambat.report_attendance_emp_terlambat_xlsx').report_action(self, data=data)