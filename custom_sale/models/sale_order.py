from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime

class sale_order(models.Model):
    _inherit = 'sale.order'

    customer_id = fields.Char(string='Customer ID', store=True)
    bill_cycle = fields.Char(string='Bill Cycle', store=True)
    invoice_id = fields.Char(string='Invoice Id', store=True)
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            rec.customer_id = rec.partner_id.customer_id
    
    salesperson_signed_on = fields.Datetime(
        string="Salesperson Signed On", copy=False)
    # salesperson_signature = fields.Binary(string="Salesperson Signature", copy=False)
    salesperson_signature = fields.Binary(related="user_id.sign_signature")

    # @api.onchange('salesperson_signature')
    # def _onchange_salesperson_signature(self):
    #     for record in self:
    #         record.salesperson_signed_on = datetime.now() if record.salesperson_signature else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'customer_id' in vals:
                dtCustByID = self.env['res.partner'].search([('customer_id','=',vals['customer_id'])],limit=1)
                if dtCustByID:
                    vals['partner_id'] = dtCustByID.id

        res =  super().create(vals_list)
        for record in res:
            record._onchange_amount_total_approval_type()
        return res


    # for approval
    state = fields.Selection(selection_add=[
        ('draft_quot','Draft Quotation'),
        ('to approve','To Approve'),
        ('draft','Approved Quotation'), 
        ('sent',),
    ], default="draft_quot")


    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].sudo().search([('model_id.model', '=', self._name)], order="id asc", limit=1)
        return dt.id if dt else False

    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'sale.order')], default=_default_loa)
    approval_info_ids = fields.Many2many(
            'approval.info',
            'approval_info_sale_rel',
            'sale_id',
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
            if rec.next_approve_user_id and rec.state == 'to approve':
                rec.is_user_approve_now = rec.next_approve_user_id == self.env.user

    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['to approve','draft_quot']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break


    @api.onchange('loa_type','amount_total')
    def _onchange_loa_type(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.loa_type:
                if rec.loa_type.is_amount:
                    if rec.amount_total >= rec.loa_type.from_amount and rec.amount_total <= rec.loa_type.to_amount:
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


    # @api.depends('tax_totals','order_line')
    @api.onchange('amount_total','order_line')
    def _onchange_amount_total_approval_type(self):
        for record in self:
            if record.amount_total:
                dtApprvl = self.env['level.approval'].search([
                    ('model_id.model', '=', self._name),
                    ('from_amount','<=',record.amount_total),
                    ('to_amount','>=',record.amount_total)
                ], limit=1)
                if dtApprvl:
                    self.loa_type = dtApprvl.id
        

    def send_schedule_activity(self):
        for record in self:
            if record.state == 'to approve':
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






    ###############################################################
    ##   BUTTON ACTION
    ###############################################################     
    def action_draft(self):
        res = super(sale_order, self).action_draft()
        for record in self:
            record.write({'state': 'draft_quot'})
            
            # set is approve to false
            for info in record.approval_info_ids.filtered(lambda x: x.is_approve):
                info.is_approve = False
            
            record._onchange_loa_type()
            
        return res
    

    def _action_cancel(self):
        res = super(sale_order, self)._action_cancel()
        for activity in self.activity_ids:
            activity.unlink()
        return res


    def button_rfa(self):
        for record in self:
            if record.loa_type:
                record._onchange_loa_type()
                # set salesperson signature
                okey = self._context.get('okey',False)
                signature = self._context.get('signature',False)

                if not okey:
                    context = {
                        'default_signature': self.env.user.sign_signature,
                        'default_data_id':self.id,
                        'default_model_name':self._name,
                        'default_function_name':"button_rfa",
                        # 'default_function_parameter':record.,
                    }
                    return{
                        'type':'ir.actions.act_window',
                        'name':'Insert Your Signature',
                        'res_model':'sign.wizard',
                        'view_type':'form',
                        'view_id': self.env.ref('custom_sale.sign_wizard_form_view').id,
                        'view_mode':'form',
                        'target':'new',
                        'context':context                
                        }
                
                if signature and signature != record.user_id.sign_signature:
                    record.user_id.sudo().write({
                        'sign_signature' : signature
                    })

                record.write({'state': 'to approve','salesperson_signed_on':datetime.now()})
                record.send_schedule_activity()

    def button_reject(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':self.id,
                    'default_model_name':self._name,
                    'default_function_name':"button_reject",
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

            # record.message_post(body=f'Reject Reason : <b>{message}</b>')
            # SET TO DRAFT
            record.write({'state': 'draft_quot'})
            
            # set is approve to false
            for info in record.approval_info_ids.filtered(lambda x: x.is_approve):
                info.is_approve = False
            
            record._onchange_loa_type()
    
    def button_multi_reject(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to approve'):
            record.with_context({'okey':True}).button_reject()

    def button_multi_approve(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to approve'):
            record.button_approve()

    def button_approve(self, force=False):
        for record in self:
            # okey = self._context.get('okey',False)
            # signature = self._context.get('signature',False)

            # if not okey:
            #     context = {
            #         'default_signature': self.env.user.sign_signature,
            #         'default_data_id':self.id,
            #         'default_model_name':self._name,
            #         'default_function_name':"button_approve",
            #         # 'default_function_parameter':record.,
            #     }
            #     return{
            #         'type':'ir.actions.act_window',
            #         'name':'Insert Your Signature',
            #         'res_model':'sign.wizard',
            #         'view_type':'form',
            #         'view_id': self.env.ref('custom_sale.sign_wizard_form_view').id,
            #         'view_mode':'form',
            #         'target':'new',
            #         'context':context                
            #         }
            
            # if signature and signature != self.env.user.sign_signature:
            #     self.env.user.sudo().write({
            #         'sign_signature' : signature
            #     })

            maxSeq = None if not record.loa_type else max(record.approval_info_ids.mapped('sequence'))
            lastApprove = True if not record.loa_type else False

            # origin code
            # maxSeq = max(record.approval_info_ids.mapped('sequence'))
            # lastApprove = False

            if record.approval_info_ids and record.state == 'to approve':
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
                record.write({'state': 'draft'})

            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            if not lastApprove:
                record.send_schedule_activity()