from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'


    # UNTUK APPROVAL

    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].sudo().search([('model_id.model', '=', self._name)], order="id asc", limit=1)
        return dt.id if dt else False

    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'purchase.request')], default=_default_loa)
    approval_info_ids = fields.Many2many(
            'approval.info',
            'approval_info_pr_rel',
            'pr_id',
            'approval_id', 
            string='Approval Information', store=True)
    next_approve_user_id = fields.Many2one('res.users', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    is_amount = fields.Boolean(string="Range Amount", store=True)
    from_amount = fields.Float(string='From Amount', store=True)
    to_amount = fields.Float(string='To Amount', store=True)

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.is_user_approve_now = False
            if rec.next_approve_user_id and rec.state == 'to_approve':
                rec.is_user_approve_now = rec.next_approve_user_id == self.env.user

    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['to_approve','draft']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break


    @api.onchange('loa_type','estimated_cost')
    def _onchange_loa_type(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.loa_type:
                if rec.loa_type.is_amount:
                    if rec.estimated_cost >= rec.loa_type.from_amount and rec.estimated_cost <= rec.loa_type.to_amount:
                        rec.is_amount = rec.loa_type.is_amount
                        rec.from_amount = rec.loa_type.from_amount
                        rec.to_amount = rec.loa_type.to_amount
                    else:
                        raise ValidationError("Total Order tidak sesuai dengan range amount pada Approval Type")
                dtLine = self.env['level.approval.line'].search([('loa_id','=',rec.loa_type.id)], order='sequence asc')
                for i in dtLine:
                    tmp = [0,0,{
                        'sequence': i.sequence,
                        'loa_id': i.loa_id.id,
                        'model_id': self.loa_type.model_id.id,
                        'trx_id': False,
                        'description': i.description,
                        'user_id': i.user_id.id,
                        'is_approve': False,
                        'approve_user_id': False,
                        'approve_date': False,
                        # 'approver_sign': False,
                    }]
                    app_inf.append(tmp)
            rec.approval_info_ids = app_inf


    @api.onchange('estimated_cost','line_ids')
    def _onchange_estimated_cost_approval_type(self):
        for record in self:
            if record.estimated_cost:
                dtApprvl = self.env['level.approval'].search([
                    ('model_id.model', '=', self._name),
                    ('from_amount','<=',record.estimated_cost),
                    ('to_amount','>=',record.estimated_cost)
                ], limit=1)
                if dtApprvl:
                    self.loa_type = dtApprvl.id
        

    def send_schedule_activity(self):
        for record in self:
            if record.state == 'to_approve':
                todos = {
                    'res_id': record.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)]).id,
                    'user_id': record.next_approve_user_id.id,
                    'summary': 'Request Approval',
                    'note': 'Hi. Please approve this record',
                    'activity_type_id': 4,
                    'date_deadline': datetime.now(),
                }
                self.env['mail.activity'].sudo().create(todos)


    @api.model_create_multi
    def create(self, vals_list):
        res =  super().create(vals_list)
        for record in res:
            record._onchange_loa_type()
        return res
    
    ###############################################################
    ##   BUTTON ACTION
    ###############################################################     
    def button_draft(self):
        res = super(PurchaseRequest, self).button_draft()
        for record in self:
            # set is approve to false
            for info in record.approval_info_ids.filtered(lambda x: x.is_approve):
                info.is_approve = False
            
            record._onchange_loa_type()

            for activity in self.activity_ids:
                activity.unlink()
        return res


    def button_to_approve(self):
        res = super(PurchaseRequest, self).button_to_approve()
        for record in self:
            if record.loa_type:
                record.send_schedule_activity()

    def button_rejected(self):
        res = super(PurchaseRequest, self).button_rejected()
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':self.id,
                    'default_model_name':self._name,
                    'default_function_name':"button_rejected",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Insert Your Reason',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_sale.revise_wizard_form_view').id,
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
            
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback=f'Reject Reason : {message}')

            # set is approve to false
            for info in record.approval_info_ids.filtered(lambda x: x.is_approve):
                info.is_approve = False
            
            record._onchange_loa_type()
    
    def button_multi_reject(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to_approve'):
            record.with_context({'okey':True}).button_rejected()

    def button_multi_approve(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to_approve'):
            record.button_approved()

    def button_approved(self, force=False):
        for record in self:
            maxSeq = None if not record.loa_type else max(record.approval_info_ids.mapped('sequence'))
            lastApprove = True if not record.loa_type else False

            # origin code
            # maxSeq = max(record.approval_info_ids.mapped('sequence'))
            # lastApprove = False

            if record.approval_info_ids and record.state == 'to_approve':
                for i in record.approval_info_ids:
                    if not i.is_approve:
                        i.write({
                            'is_approve': True,
                            'approve_user_id': self.env.user.id,
                            'approve_date': datetime.now(),
                        })
                        lastApprove = i.sequence == maxSeq
                        break

            if lastApprove:
                record.write({'state': 'approved'})

            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            if not lastApprove:
                record.send_schedule_activity()