from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approved', 'Approved'),
    ('done', 'Done'),
    ('cancel','Canceled'),
    ('refuse','Refuse'),
    ('revise','Revise'),
    ('processing','HR Processing'),
    ('not_recommended','Not Recommended'),
    ('recommended','Recommended'),
]

class MatrixApproval(models.Model):
    _name = "matrix.approval"
    _description = "Matrix Approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "display_name"

    name = fields.Char(string='Matrix Approval', required=True, tracking=True)
    display_name = fields.Char(string='Name', compute='_compute_display_name')
    model_id = fields.Many2one('ir.model', string='Model', tracking=True, ondelete='cascade', readonly=True)
    model_name = fields.Char(string="Model Name")
    department_ids = fields.Many2many('hr.department', string='Specific Department', required=True, tracking=True)
    job_ids = fields.Many2many('hr.job', string='Specific Job Position', tracking=True)
    active = fields.Boolean(default=True)

    matrix_line = fields.One2many('matrix.approval.line','matrix_id', string="Matrix Approval Lines", ondelete='cascade', copy=True, tracking=True)

    @api.constrains('job_ids','department_ids')
    def _constrains_job_ids(self):
        for record in self:
            if record.job_ids:
                model_context = self.env.context.get('model_yg_tampil')
                domain = [
                    ('id','!=',record.id),
                    ('department_ids.id','in',record.department_ids.ids),
                    ('job_ids.id','in',record.job_ids.ids),
                    ('active','=',True),
                    ('model_id','!=',False)
                ]
                if record.model_id:
                    domain.append(('model_id','=',record.model_id.id))
                else:
                    domain.append(('model_id.name','=',model_context))
                matrix_id = self.env[self._name].search(domain)
                if matrix_id:
                        raise ValidationError(f"Job Tersebut sudah ada di master approval yang lain!\n\n{matrix_id[0].name}")
                    
    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    @api.onchange('model_name')
    def _onchange_model_name(self):
        for rec in self:
            dtModel = self.env['ir.model'].search([('name', '=', rec.model_name)])
            rec.model_id = dtModel.id if dtModel else False

    def initial_sequence(self):
        idx = 0
        for i in self.matrix_line:
            i.write({'sequence': i.sequence + idx})
            idx += 1
                
    @api.model
    def create(self, vals):        
        model_context = self.env.context.get('model_yg_tampil')
        model_context_id = self.env['ir.model'].search([('name', '=', model_context)])
        if model_context_id:
            vals['model_id'] = model_context_id.id

        res = super(MatrixApproval, self).create(vals)
        res.initial_sequence()
        return res
    
    def write(self, vals):
        res = super(MatrixApproval, self).write(vals)
        return res
    
class MatrixApprovalLine(models.Model):
    _name = "matrix.approval.line"
    _description = "Matrix Approval Line"
    _rec_name = "description"

    matrix_id = fields.Many2one('matrix.approval',  string='Matrix Approval', readonly=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    description = fields.Char(string='Approval Name', tracking=True)
    group_id = fields.Many2one('res.groups', string='Group',  required=True) # domain=_get_group_id_domain,
    @api.onchange('group_id')
    def domain_user_ids(self):
        domain = {}
        if self.group_id:
            list_user = self.group_id.users.ids
            domain = {'domain': {'user_ids': [('id', 'in', list_user)]}}
        return domain
    user_ids = fields.Many2many('res.users', 'matrix_approval_line_res_user', 'matrix_approval_line_id', 'user_id', string='Spesific Employee (If Exist)', tracking=True)
    need_reason = fields.Boolean('Need fill reason when approve?')

    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True, related=False) # related='user_id.employee_id.job_id',

class MatrixApprovalInformation(models.Model):
    _name = "matrix.approval.info"
    _description = "Matrix Approval Information"

    matrix_id = fields.Many2one('matrix.approval',  string='Matrix Approval', copy=False)
    matrix_line_id = fields.Many2one('matrix.approval.line',  string='Layer / Stage Approval', copy=False)
    model_id = fields.Many2one('ir.model', string='Model', ondelete="cascade", index=True, tracking=True)
    trx_id = fields.Integer(string='Transaction Id')
    sequence = fields.Integer(string='Sequence', tracking=True)
    state = fields.Selection(STATE, string='State')    

    # loa line
    description = fields.Char(string='Approval Name', tracking=True)
    approve_description = fields.Char(string='Reason', tracking=True)
    user_ids = fields.Many2many('res.users', 'matrix_approval_info_res_user', 'matrix_approval_line_id', 'user_id', string='User', tracking=True)
    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True, related=False) # related='user_id.employee_id.job_id'
    
    group_id = fields.Many2one('res.groups', string='Group') # domain=_get_group_id_domain,
    
    # approve information
    is_approve = fields.Boolean(string="Is Approve", default=False)
    approve_user_id = fields.Many2one('res.users', string='Pelaksana')
    approve_dept_id = fields.Many2one('hr.department', string='Department', related="approve_user_id.employee_id.department_id")
    approve_job_id = fields.Many2one('hr.job', string='Position', related="approve_user_id.employee_id.job_id")
    approve_date = fields.Datetime(string="Tanggal")
    approver_sign = fields.Char('Signature', readonly=True)