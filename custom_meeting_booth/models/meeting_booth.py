# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime,timedelta,date

class MasterMeetingBooth(models.Model):
    _name = "master.meeting.booth"

    sequence = fields.Integer()
    name = fields.Char(string="Name", required=True, tracking=True)
    active = fields.Boolean(default=True)

class MeetingBooth(models.Model):
    _name = "meeting.booth"

    name = fields.Char(string="Name", tracking=True, compute='_compute_name')
    @api.depends('booth_id', 'employee_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{} @ {}".format(rec.employee_id.name, rec.booth_id.name)

    booth_id = fields.Many2one('master.meeting.booth', string='Booth', ondelete='restrict', 
                                required=True, group_expand='_group_booth', 
                                domain=[('active','=',True)])
    @api.model
    def _group_booth(self,stages,domain,order):
        columns_ids = self.env['master.meeting.booth'].search([])
        return columns_ids

    def _default_start_date(self):
        return datetime(datetime.now().year, datetime.now().month, datetime.now().day, 1, 0)
    date_start = fields.Datetime(string='Start Date', default=_default_start_date, required=True)

    def _default_end_date(self):
        return datetime(datetime.now().year, datetime.now().month, datetime.now().day, 10, 0)
    date_end = fields.Datetime(string='End Date', default=_default_end_date, required=True)
    
    def _default_employee_id(self):
        return self.env.user.employee_id.id
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_id)
    
    note = fields.Text(string='Note')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft')], default='draft')
    
    time_display = fields.Char(compute="_compute_date_display")
    date_display = fields.Char(compute="_compute_date_display")
    @api.depends('date_start', 'date_end')
    def _compute_date_display(self):
        for rec in self:
            rec.date_display = "{}".format((rec.date_start + timedelta(hours=7)).strftime("%d %b %Y"))
            rec.time_display = "{} to {}".format((rec.date_start + timedelta(hours=7)).strftime("%H:%M"), (rec.date_end + timedelta(hours=7)).strftime("%H:%M"))
    
    @api.constrains('date_start','date_end')
    def _constrains_datetime_overlap(self):
        for rec in self:
            timeExist = self.env['meeting.booth'].search([
                ('date_start','>=',datetime(rec.date_start.year, rec.date_start.month, rec.date_start.day, 0, 0)),
                ('date_start','<=',datetime(rec.date_start.year, rec.date_start.month, rec.date_start.day, 23, 59)),
                ('booth_id','=',rec.booth_id.id),
                ('id','!=', rec.id)])
            print("len(timeExist) = ", len(timeExist))
            for i in timeExist:
                if rec.date_start >= i.date_start and rec.date_start <= i.date_end:
                    raise UserError("Meeting booth already taken by another employee. \n Choose another time.")

    @api.model
    def create(self, vals):
        result = super(MeetingBooth, self).create(vals)
        return result
    
