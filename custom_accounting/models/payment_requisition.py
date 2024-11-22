from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from num2words import num2words

class AccontPaymentRequisition(models.Model):
    _name = "account.payment.requisition"
    _description = "Payment Requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "pr_date desc"

    # main data
    name = fields.Char(string='Name', required=True, tracking=True, default=lambda self: ('New'))
    pr_date = fields.Date(required=True, string="Date", default=fields.Datetime.now, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Pemasok",
        store=True, readonly=False, ondelete='restrict', required=True,
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        tracking=True, check_company=True)
    ref = fields.Char(string="Memo", tracking=True)
    no_voucher = fields.Char(string="Voucher", tracking=True)

    # selection from config accounting
    method_id = fields.Many2one('payment.method', string="Payment Method", required=True, tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal', check_company=True, required=True,
        domain="[('type', 'in', ('bank','cash')), ('company_id', '=', company_id), ('id', '!=', journal_id)]", tracking=True)
    partner_bank_id = fields.Many2one('res.partner.bank', string="Vendor Bank Account", readonly=False, store=True, tracking=True,
        domain="[('partner_id', '=', partner_id)]", check_company=True, compute="_compute_partner_bank_id")
    
    # all abount monetary
    amount = fields.Monetary(currency_field='currency_id', digits='Product Price', tracking=True)
    grand_amount = fields.Monetary(currency_field='currency_id', digits='Product Price', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id',
        help="The payment's currency.")
    
    # others field
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True, compute='_compute_company_id')
    payment_id = fields.Many2one('account.payment', store=True, tracking=True)
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'), 
            ('cancel', 'Cancelled'),
            ('refuse','Refused'),
            ('to approve', 'To Approve'),
            ('approved', 'Approved'),
            ], default='draft')
    
    # detail relation
    pr_line = fields.One2many('account.payment.requisition.line','pr_id', string="Payment Requisition Line", ondelete='cascade', copy=True, tracking=True)
    pr_potongan_line = fields.One2many('account.payment.requisition.line.potongan','pr_id', string="Payment Requisition Line Potongan", ondelete='cascade', copy=True, tracking=True)
    
    original_move_ids = fields.Many2many('account.move', 'asset_move_rel', 'pr_id', 'move_id', string='Vendor Bills', required=True,
        domain="[('move_type','=','in_invoice'), ('state','=','posted'), ('partner_id','=',partner_id), ('payment_state','not in',['paid'])]")

    # @api.constrains('original_move_ids')
    # def _constrains_original_move_ids(self):
    #     for rec in self:
    #         if not rec.original_move_ids:
    #             raise UserError("Belum ada Vendor Bills yang diinput.")
                
    # Kebutuhan Approval
    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].search([('model_id.model', '=', 'account.payment.requisition')], order="id asc", limit=1)
        return dt.id if dt else False
    
    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'account.payment.requisition')], required=True, default=_default_loa)
    approval_info_ids = fields.Many2many('approval.info','payment_requisition_approval_line','pr_id','approval_id', 
                                         string='Approval Information', store=True)
    next_approve_user_id = fields.Many2one('res.users', string='Next Approval', tracking=True, compute="_compute_next_approval", store=True)
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    is_amount = fields.Boolean(string="Range Amount", store=True, readonly=True)
    from_amount = fields.Float(string='From Amount', store=True, readonly=True, digits='Product Price')
    to_amount = fields.Float(string='To Amount', store=True, readonly=True, digits='Product Price')

    # global func
    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.is_user_approve_now = False
            if rec.next_approve_user_id and rec.state == 'to approve':
                rec.is_user_approve_now = rec.next_approve_user_id == self.env.user

    def _format_currency(self, value=None, separator='.', p2w=False):
        value = self.amount_untaxed if not value and value != 0.0 else value
        value = int(value) if int(value) == value else value
        if not p2w:
            value = '{:,}'.format(value).replace('.', '_comma_')
            value = value.replace(',', separator)
            return value.replace('_comma_', ',')
        return num2words(value, lang='id', to='currency').title()
    
    # compute func
    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['to approve']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break

    @api.depends('journal_id')
    def _compute_company_id(self):
        for move in self:
            move.company_id = move.journal_id.company_id or move.company_id or self.env.company

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.journal_id.currency_id or pay.journal_id.company_id.currency_id

    @api.depends('partner_id', 'journal_id')
    def _compute_partner_bank_id(self):
        for pay in self:
            available_partner_bank_accounts = pay.partner_id.bank_ids.filtered(lambda x: x.company_id in (False, pay.company_id))
            if available_partner_bank_accounts:
                pay.partner_bank_id = available_partner_bank_accounts[0]._origin
            else:
                pay.partner_bank_id = False
    
    # onchange func
    @api.depends('amount','grand_amount','pr_line','pr_potongan_line','original_move_ids')
    @api.onchange('amount','grand_amount','pr_line','pr_potongan_line','original_move_ids')
    def _onchange_amount_total_approval_type(self):
        if self.grand_amount:
            dtApprvl = self.env['level.approval'].search([
                ('model_id.model', '=', 'account.payment.requisition'),
                ('from_amount','<=',self.grand_amount),
                ('to_amount','>=',self.grand_amount)], limit=1)
            if dtApprvl:
                self.loa_type = dtApprvl.id

    @api.onchange('loa_type')
    def _onchange_loa_type(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.loa_type:
                if rec.loa_type.is_amount:
                    if rec.grand_amount >= rec.loa_type.from_amount and rec.grand_amount <= rec.loa_type.to_amount:
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

    @api.onchange('method_id')
    def _onchange_method_id(self):
        if self.method_id:
            self.journal_id = self.method_id.journal_id

    @api.onchange('original_move_ids')
    def _onchange_pr_line(self):
        for rec in self:
            rec.amount = sum(self.original_move_ids.mapped('amount_residual'))
            rec.grand_amount = rec.amount - sum(self.pr_potongan_line.mapped('amount'))

    @api.onchange('pr_potongan_line','amount')
    def _onchange_pr_potongan_line(self):
        for rec in self:
            rec.grand_amount = rec.amount - sum(self.pr_potongan_line.mapped('amount'))
    
    # action function
    def send_schedule_actifity(self):
        todos = {
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'account.payment.requisition')]).id,
            'user_id': self.next_approve_user_id.id,
            'summary': 'Request Approval',
            'note': 'Please approve this Payment Requisition',
            'activity_type_id': 4,
            'date_deadline': datetime.now(),
        }
        self.env['mail.activity'].sudo().create(todos)

    def button_confirm(self):
        # if self.grand_amount > sum(self.original_move_ids.mapped('amount_residual')):
        #     raise ValidationError("Grand total tidak boleh melebihi sisa total bills.")

        pr_name = self.name
        if pr_name == 'New':
            pr_name = self.env['ir.sequence'].with_context().next_by_code('payment.requisition.seq', sequence_date=self.pr_date) or ('New')

        if self.loa_type:
            self.sudo().write({
                'name': pr_name,
                'state': 'to approve'})
            self._compute_next_approval()
            self.sudo().send_schedule_actifity()
        else:
            raise UserError("Approval Type belum dipilih.")
        return

    def button_approve(self):
        maxSeq = max(self.approval_info_ids.mapped('sequence'))
        lastApprove = False
        if self.approval_info_ids and self.state == 'to approve':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    lastApprove = i.sequence == maxSeq
                    # if not lastApprove:
                    i.sudo().write({
                        'is_approve': True,
                        'approve_user_id': self.env.user.id,
                        'approve_date': datetime.now(),
                    })
                    self._compute_next_approval()
                    break

        if lastApprove:
            self.sudo().write({
                'state': 'approved'
                })
            self.create_payments()
            for activity in self.activity_ids:
                activity.sudo().action_feedback(feedback="")

            # return {
            #     'name': _('Register Payment from Payment Requisition'),
            #     'res_model': 'account.payment.register',
            #     'view_mode': 'form',
            #     'context': {
            #         'active_model': 'account.move',
            #         'active_ids': self.pr_line.move_id.ids,
            #         'default_method_id': self.method_id.id,
            #         'default_journal_id': self.journal_id.id,
            #         'default_partner_bank_id': self.partner_bank_id.id,
            #         'default_communication': self.ref,
            #         'default_payment_date': self.pr_date,
            #         'default_pr_id': self.id,
            #     },
            #     'target': 'new',
            #     'type': 'ir.actions.act_window',
            # }

        for activity in self.activity_ids:
            activity.sudo().action_feedback(feedback="")

        if not lastApprove:
            self.sudo().send_schedule_actifity()

        return 
    
    def button_register_payment(self):
        return {
            'name': _('Register Payment from Payment Requisition'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.original_move_ids.ids,
                'default_method_id': self.method_id.id,
                'default_journal_id': self.journal_id.id,
                'default_partner_bank_id': self.partner_bank_id.id,
                'default_communication': self.ref,
                'default_no_voucher': self.no_voucher,
                'default_payment_date': self.pr_date,
                'default_amount': self.grand_amount,
                'default_pr_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def create_payments(self):
        line_disc = []
        for i in self.pr_potongan_line:
            det = [0, False, {
                u'account_id': i.account_id.id,
                u'currency_id': i.currency_id.id,
                u'amount': i.amount,
                u'description': i.description,
            }]
            line_disc.append(det)

        if self.original_move_ids:
            reg_payments = self.env['account.payment.register'].sudo().with_context({
                'active_model':'account.move',
                'active_ids':self.original_move_ids.ids}
            ).create({
                'method_id':self.method_id.id,
                'journal_id':self.journal_id.id,
                'partner_bank_id':self.partner_bank_id.id,
                'communication':self.ref,
                'no_voucher':self.no_voucher,
                'payment_date':self.pr_date,
                'amount':self.amount,
                'pr_id':self.id,
                'payment_line_disc_ids': line_disc,
                'partner_id': self.partner_id.id,
            }).sudo().action_create_payments()
        else:
            reg_payments = self.env['account.payment'].sudo().create({
                'method_id':self.method_id.id,
                'journal_id':self.journal_id.id,
                'partner_bank_id':self.partner_bank_id.id,
                'ref':self.ref,
                'no_voucher':self.no_voucher,
                'date':self.pr_date,
                'amount':self.amount,
                'grand_amount':self.grand_amount,
                'payment_line_disc_ids': line_disc,
                'partner_id': self.partner_id.id,
            })
            reg_payments.sudo().action_post()
            self.sudo().write({'payment_id': reg_payments.id})
            
    def button_set_draft(self):
        if self.payment_id:
            raise UserError("Tidak dapat dilakukan, silakan hapus Payment yang sudah dibuat.")
        
        self.write({'state':'draft'})
        self._compute_next_approval()
        self.cancel_approval()

    def button_refuse(self):
        if self.payment_id:
            raise UserError("Tidak dapat dilakukan, silakan hapus Payment yang sudah dibuat.")
        
        self.write({'state':'refuse'})
        self._compute_next_approval()
        self.cancel_approval()

    def button_cancel(self):
        if self.payment_id:
            raise UserError("Tidak dapat dilakukan, silakan hapus Payment yang sudah dibuat.")
        
        self.write({'state':'cancel'})
        self._compute_next_approval()
        self.cancel_approval()

    def cancel_approval(self):
        for i in self.approval_info_ids:
            i.write({
                'is_approve': False,
                'approve_user_id': False,
                'approve_date': False,
            })

    def button_open_payment(self):
        return {
            'name': _('Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context':{
                'readonly_payment_type': True,
            }
        }

    def updateTrxId(self):
        for i in self.approval_info_ids:
            i.write({'trx_id':self.id})

    def button_user_approve(self):
        for rec in self:
            rec.button_approve()

    # create or write func
    @api.model
    def create(self, vals):
        result = super(AccontPaymentRequisition, self).create(vals)
        if 'approval_info_ids' in vals:
            result.updateTrxId()
        return result
    
    def write(self, vals):
        if self.payment_id:
            raise ValidationError("Tidak dapat mengubah data ini, karena sudah ada Pembayaran.")

        result = super(AccontPaymentRequisition, self).write(vals)
        return result
    
    def unlink(self):
        if self.payment_id:
            raise ValidationError("Tidak dapat menghapus data ini, karena sudah ada Pembayaran.")
        if self.state != 'draft':
            raise ValidationError("Tidak dapat menghapus data ini, karena status bukan draft.")

        result = super(AccontPaymentRequisition, self).unlink()
        return result
    
class AccontPaymentRequisitionLine(models.Model):
    _name = "account.payment.requisition.line"
    _description = "Payment Requisition Line"

    pr_id = fields.Many2one('account.payment.requisition',  string='Payment Requisition', readonly=True, copy=False)
    move_id = fields.Many2one('account.move', required=True, 
                              domain="[('move_type','=','in_invoice'), ('state','=','posted'), ('partner_id','=',parent.partner_id), ('payment_state','not in',['paid'])]")
    bill_date = fields.Date(string='Bill Date', related='move_id.invoice_date', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner', string='Pemasok', related='move_id.partner_id', readonly=True, store=True)
    due_date = fields.Date(string='Due Date', related='move_id.invoice_date_due', readonly=True, store=True)
    amount_total = fields.Monetary(string='Amount Total', currency_field='currency_id', readonly=True, store=True, digits='Product Price')
    amount_residual = fields.Monetary(string='Amount Due', currency_field='currency_id', readonly=True, store=True, digits='Product Price')
    currency_id = fields.Many2one('res.currency', string="Currency", related='move_id.currency_id', readonly=True, store=True)
    
    @api.onchange('move_id')
    def _onchange_move_id(self):
        if self.move_id:
            self.amount_total = self.move_id.amount_total
            self.amount_residual = self.move_id.amount_residual
    
class AccontPaymentRequisitionLinePotongan(models.Model):
    _name = "account.payment.requisition.line.potongan"

    pr_id = fields.Many2one('account.payment.requisition',  string='Payment Requisition', readonly=True, copy=False)
    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="restrict", required=True)    
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, related="pr_id.currency_id", help="The payment's currency.")
    amount = fields.Monetary(currency_field='currency_id', string='Total', digits='Amount', required=True)
    description = fields.Char(string='Description')