from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class LevelOfApproval(models.Model):
    _name = "level.approval"
    _description = "Level of Approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "display_name"

    name = fields.Char(string='Level of Approval', required=True, tracking=True)
    display_name = fields.Char(string='Nama', compute='_compute_display_name')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete="cascade", index=True, tracking=True)
    is_amount = fields.Boolean(string="Range Amount", default=False)
    from_amount = fields.Float(string='From Amount', default=0)
    to_amount = fields.Float(string='To Amount', default=0)
    is_for_cost_sheet = fields.Boolean('Is For Cost Sheet')
    
    loa_line = fields.One2many('level.approval.line','loa_id', string="Level of Approval Lines", ondelete='cascade', copy=True, tracking=True)

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            if rec.is_amount:
                rec.display_name = str(rec.name) + ' (Dari ' + str(f'{rec.from_amount:,.0f}')  + ' s/d ' + str(f'{rec.to_amount:,.0f}') + ')'
            else:
                rec.display_name = rec.name

    def initial_sequence(self):
        idx = 0
        for i in self.loa_line:
            i.write({'sequence': i.sequence + idx})
            idx += 1

    @api.model
    def create(self, vals):
        res = super(LevelOfApproval, self).create(vals)
        res.initial_sequence()
        return res
    
    def write(self, vals):
        res = super(LevelOfApproval, self).write(vals)
        return res
    
class LevelOfApprovalLine(models.Model):
    _name = "level.approval.line"
    _description = "Level of Approval Line"

    loa_id = fields.Many2one('level.approval',  string='Level of Approval', readonly=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    description = fields.Char(string='Approval Name', tracking=True)
    user_ids = fields.Many2many('res.users', 'approval_line_res_user', 'approval_line_id', 'user_id', string='User', tracking=True)
    
    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True, related=False) # related='user_id.employee_id.job_id',

class ApprovalInformation(models.Model):
    _name = "approval.info"
    _description = "Approval Information"

    loa_id = fields.Many2one('level.approval',  string='Level of Approval', copy=False)
    model_id = fields.Many2one('ir.model', string='Model', ondelete="cascade", index=True, tracking=True)
    trx_id = fields.Integer(string='Transaction Id')
    sequence = fields.Integer(string='Sequence', tracking=True)

    # loa line
    description = fields.Char(string='Approval Name', tracking=True)
    approve_description = fields.Char(string='Description', tracking=True)
    user_ids = fields.Many2many('res.users', 'approval_info_res_user', 'approval_line_id', 'user_id', string='User', tracking=True)
    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True, related=False) # related='user_id.employee_id.job_id'

    # approve information
    is_approve = fields.Boolean(string="Is Approve", default=False)
    approve_user_id = fields.Many2one('res.users', string='Approved By')
    approve_date = fields.Datetime(string="Approval Date")
    approver_sign = fields.Char('Signature', readonly=True)