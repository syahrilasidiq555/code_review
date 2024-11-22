from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    company_address = fields.Text(string="Company Address")
    boss_name = fields.Text(string="Boss Name")
    first_position = fields.Char(string="First Position")
    last_Position = fields.Char(string="Last Position")
    desc_position = fields.Text(string="Description of Position")
    leave_reason = fields.Text(string="Leave Reason")
    verklaring = fields.Boolean(string="Verklaring ?")
    # verklaring_file = fields.Binary(string='Verklaring File', attachment=True)
    verklaring_file = fields.Many2many('ir.attachment','attachment_rel_verklaring','verklaring_file_id','verklaring_file_attach_id', string='Verklaring Attachments') 
    last_salary = fields.Float(string="Last Salary")