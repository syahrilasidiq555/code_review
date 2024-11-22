from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

class hr_surat_peringatan(models.Model):
    _name = 'hr.surat.peringatan'

    @api.constrains('date_start','date_end')
    def _constrains_date(self):
        for rec in self:
            if not rec.date_start: 
                raise ValidationError("Date start must be filled.")
            if not rec.date_end: 
                raise ValidationError("Date end must be filled.")

    sp_type = fields.Selection(
        string='SP Type',
        selection=[
            ('teguran', 'Teguran'), 
            ('sp1', 'SP 1'),
            ('sp2', 'SP 2'),
            ('sp3', 'SP 3'),
        ], default='teguran')
    employee_id = fields.Many2one('hr.employee',string='Employee', required=True)    
    pelanggaran = fields.Char(string="Pelanggaran")
    date_start = fields.Date(string="Date Start", store=True)
    date_end = fields.Date(string="Date End", store=True)
    file = fields.Binary(string='File', attachment=True)
    file_ids = fields.Many2many('ir.attachment','attachment_peringatan_rel','peringatan_id','attachment_id', string='Attachments')
    state = fields.Selection(
        string='State',
        selection=[
            ('not_active', 'Not Active'), 
            ('active', 'Active'), 
            ('expired', 'Expired'),
        ], compute='_compute_state', store=False)
        
    @api.depends()
    def _compute_state(self):
        def switch_state(start, end):
            ayeuna = datetime.now().date()
            switcher = {
                ayeuna < start : 'not_active',
                ayeuna >= start and ayeuna <= end : 'active',
                ayeuna > end : 'expired',
	        }
            return switcher.get(True, "Date Not Valid :(")
            
        for rec in self:
            try:
                if rec.date_start and rec.date_end: rec.state = switch_state(rec.date_start, rec.date_end)
            except:
                pass
            