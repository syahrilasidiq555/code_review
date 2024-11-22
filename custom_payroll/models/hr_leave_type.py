from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil import relativedelta

class hr_leave_type(models.Model):
    _inherit = 'hr.leave.type'

    is_affect_attendance_incentive = fields.Boolean('Affected to Attendance Incentive')
    is_affect_base_salary = fields.Boolean('Affected to Base Salary')