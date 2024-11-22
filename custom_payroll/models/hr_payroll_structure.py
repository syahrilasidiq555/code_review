# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'


    pembagi_hari = fields.Integer(string='Pembagi Hari')