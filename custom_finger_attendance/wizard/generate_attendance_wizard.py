from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class generate_attendance_wizard(models.TransientModel):
    _name = "generate.attendance.wizard"

    work_time = fields.Selection([
        ('normal', 'Normal'),
        ('shift3', 'Shift 3'),
    ], string='Work Time', required=True, default='normal')
    finger_config_id = fields.Many2one('finger.attendance.config', string='Finger Attendance Config', required=True)
    attendance_date = fields.Date(string='Attendance Date', required=True)
    

    def btn_continue(self):
        for record in self:
            if record.finger_config_id and record.attendance_date:
                record.finger_config_id.action_get_attendance(record.attendance_date,shift3=True if record.work_time == 'shift3' else False)