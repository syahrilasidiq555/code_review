from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from datetime import date, datetime

import sys

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].search([('model_id.model', '=', 'purchase.order')], order="id asc", limit=1)
        return dt.id if dt else False

    # Kebutuhan Approval
    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'purchase.order')], default=_default_loa)
    approval_info_ids = fields.Many2many('approval.info','purchase_approval_line','purchase_id','approval_id', 
                                         string='Approval Information', store=True)
    next_approve_user_id = fields.Many2one('res.users', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    is_amount = fields.Boolean(string="Range Amount", store=True)
    from_amount = fields.Float(string='From Amount', store=True)
    to_amount = fields.Float(string='To Amount', store=True)

    # domain is_vendor = true
    partner_id = fields.Many2one(domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_vendor', '=', True)]", )

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.is_user_approve_now = False
            if rec.next_approve_user_id and rec.state == 'to approve':
                rec.is_user_approve_now = rec.next_approve_user_id == self.env.user

    @api.onchange('loa_type')
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
                        'approver_sign': False,
                    }]
                    app_inf.append(tmp)
            rec.approval_info_ids = app_inf

    @api.depends('tax_totals_json','order_line')
    @api.onchange('tax_totals_json','order_line')
    def _onchange_amount_total_approval_type(self):
        if self.tax_totals_json:
            dtApprvl = self.env['level.approval'].search([('model_id.model', '=', 'purchase.order'),('from_amount','<=',self.amount_total),('to_amount','>=',self.amount_total)], limit=1)
            if dtApprvl:
                self.loa_type = dtApprvl.id
    
    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['to approve','draft','sent']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break

    def send_schedule_actifity(self):
        if self.state == 'to approve':
            todos = {
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id,
                'user_id': self.next_approve_user_id.id,
                'summary': 'Request Approval',
                'note': 'Hi. Please approve this order',
                'activity_type_id': 4,
                'date_deadline': datetime.now(),
            }
            self.env['mail.activity'].sudo().create(todos)

    def generate_nomor_purchase_baru(self, date_order):
        name = self.env['ir.sequence'].with_context().next_by_code('purchase.order.confirm', sequence_date=date_order) or _('New')
        self.sudo().write({'purchase_name':name})
        return
    
    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.loa_type:
            if self.state == 'draft':
                self.write({'state': 'sent'})
            elif self.state == 'sent':
                self.write({'state': 'to approve'})
                self.send_schedule_actifity()
        return res

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        return res

    ###############################################################
    ##   OVERRIDE METHOD
    ###############################################################     
    def button_approve(self, force=False):
        # edit syahril, kalau ada cost sheet & tidak ada approval maka di skip
        maxSeq = None if self.cost_sheet_id and not self.loa_type else max(self.approval_info_ids.mapped('sequence'))
        lastApprove = True if self.cost_sheet_id and not self.loa_type else False

        # origin code
        # maxSeq = max(self.approval_info_ids.mapped('sequence'))
        # lastApprove = False

        if self.approval_info_ids and self.state == 'to approve':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    i.write({
                        'is_approve': True,
                        'approve_user_id': self.env.user.id,
                        'approve_date': datetime.now(),
                    })
                    lastApprove = i.sequence == maxSeq
                    break

        if lastApprove:
            self = self.filtered(lambda order: order._approval_allowed())
            self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
            self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
            # diambil dari module purchase_stock
            self._create_picking()
            if self.purchase_name == 'New':
                self.generate_nomor_purchase_baru(self.date_order)

        for activity in self.activity_ids:
            activity.action_feedback(feedback="")

        if not lastApprove:
            self.send_schedule_actifity()

        return {}
    
    def updateTrxId(self):
        for i in self.approval_info_ids:
            i.write({'trx_id':self.id})

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if 'approval_info_ids' in vals:
            res.updateTrxId()
        return res