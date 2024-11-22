from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta, date
import json

class CashAdvance(models.Model):
    _name = 'cash.advance'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Cash Advance"
    

    def _get_company_domain(self):
        domain = []
        if self.env.user.id:
            query ="select cid from res_company_users_rel where user_id = {user_id}"
            self.env.cr.execute(query.format(
                user_id = self.env.user.id
            ))
            ids = self.env.cr.fetchall()
            domain = [('id','in',[x[0] for x in ids])]
            # raise ValidationError(query,ids)
        return domain

    def _set_default_company(self):
        return self.env.user.company_id.id
    
    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].search([('model_id.model', '=', 'cash.advance')], order="id asc", limit=1)
        return dt.id if dt else False

    name = fields.Char(string='Name',tracking=True)

    parent_id = fields.Many2one('cash.advance', string='Parent')

    employee_id = fields.Many2one('hr.employee', string='Karyawan', required=True, tracking=True)
    department_id = fields.Many2one(related="employee_id.department_id", string="Departemen", store=True)
    # job_id = fields.Many2one(related="employee_id.job_id", string="Posisi", store=True)
    
    
    # Kebutuhan Approval
    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'cash.advance')], required=True, default=_default_loa)
    approval_info_ids = fields.Many2many('approval.info','cash_advance_approval_line','cash_advance_id','approval_id', 
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
            if rec.next_approve_user_id and rec.state == 'confirm':
                rec.is_user_approve_now = rec.next_approve_user_id == self.env.user

    @api.onchange('loa_type')
    def _onchange_loa_type(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.loa_type:
                if rec.loa_type.is_amount:
                    if rec.total_amount >= rec.loa_type.from_amount and rec.total_amount <= rec.loa_type.to_amount:
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

    @api.depends('total_amount','line_ids')
    @api.onchange('total_amount','line_ids')
    def _onchange_amount_total_approval_type(self):
        if self.total_amount:
            dtApprvl = self.env['level.approval'].search([('model_id.model', '=', 'cash.advance'),('from_amount','<=',self.total_amount),('to_amount','>=',self.total_amount)], limit=1)
            if dtApprvl:
                self.loa_type = dtApprvl.id

    @api.depends('state','approval_info_ids','approval_info_ids.is_approve')
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['confirm']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break

    def updateTrxId(self):
        for i in self.approval_info_ids:
            i.write({'trx_id':self.id})

    def cancel_approval(self):
        for i in self.approval_info_ids:
            i.write({
                'is_approve': False,
                'approve_user_id': False,
                'approve_date': False,
            })    

    def send_schedule_actifity(self):
        todos = {
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'cash.advance')]).id,
            'user_id': self.next_approve_user_id.id,
            'summary': 'Request Approval',
            'note': 'Hi. Please approve this order',
            'activity_type_id': 4,
            'date_deadline': datetime.now(),
        }
        self.env['mail.activity'].sudo().create(todos)

    date = fields.Date(string='Tanggal', default=datetime.now().date(), required=True, tracking=True)
    product_id = fields.Many2one('product.product', string='Produk', required=True, tracking=True)
    uom_id = fields.Many2one(related="product_id.uom_id", store=True)
    desc = fields.Text('Deskripsi', required=True, tracking=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.desc = record.product_id.display_name

    qty = fields.Float('Quantity', required=True, default=1, digits="Product Unit of Measure", tracking=True)
    amount = fields.Monetary(string='Amount', digits='Product Price', required=True, tracking=True)
    total_amount = fields.Monetary(compute='_compute_total_amount', string='Total Amount', digits='Product Price', default=0.0, store=True, tracking=True)

    @api.depends('product_id','qty','amount')
    def _compute_total_amount(self):
        for record in self:
            total_amount = 0
            if record.qty and record.amount:
                total_amount = record.qty * record.amount
            record.total_amount = total_amount

    real_qty = fields.Float('Realisasi Quantity', default=1, digits="Product Unit of Measure", tracking=True)
    real_amount = fields.Monetary(string='Realisasi Amount', digits='Product Price', tracking=True)
    real_total_amount = fields.Monetary(compute='_compute_real_total_amount', string='Total Realisasi Amount', digits='Product Price', default=0.0, store=True, tracking=True)

    @api.depends('product_id','real_qty','real_amount')
    def _compute_real_total_amount(self):
        for record in self:
            real_total_amount = 0
            if record.real_qty and record.real_amount:
                real_total_amount = record.real_qty * record.real_amount
            record.real_total_amount = real_total_amount

    status_ca = fields.Selection([
        ('normal', 'Normal'),
        ('kurang', 'Kurang Bayar'),
        ('lebih', 'Lebih Bayar'),
    ], string='Status Cash Advance', compute='_compute_status_ca', store=True)
    @api.depends('total_amount','real_total_amount')
    def _compute_status_ca(self):
        for record in self:
            record.status_ca = False
            
            if record.state == 'approve':
                if record.total_amount == record.real_total_amount:
                    record.status_ca = 'normal'
                    record.state = 'done'
                elif record.total_amount < record.real_total_amount:
                    record.status_ca = 'kurang'
                elif record.total_amount > record.real_total_amount:
                    record.status_ca = 'lebih'
    
    is_returned = fields.Boolean(string='Is Returned', default=False, compute='_compute_is_returned', store=True)
    
    @api.depends('status_ca','payment_ids','payment_ids.state')
    def _compute_is_returned(self):
        for record in self:
            is_returned = False
            if record.payment_ids.filtered(lambda x: x.payment_type == 'inbound'):
                is_returned = True
            record.is_returned = is_returned

    account_id = fields.Many2one('account.account', string='Account', required=True,
        domain="[('user_type_id.type','=','payable')]")
    method_id = fields.Many2one('payment.method', string="Payment Method", required=True)
    journal_id = fields.Many2one(related="method_id.journal_id")

    bill_id = fields.Many2one('account.move', string='Bill')
    bill_id_payment_state = fields.Selection(related="bill_id.payment_state")
    
    payment_ids = fields.Many2many("account.payment",
        "cash_advance_payments",
        "payment_id",
        "cash_advance_id", string='payment')

    payment_ids_count = fields.Integer(compute='_compute_payment_ids_count', string='Payment IDs Count')
    
    @api.depends('payment_ids','state')
    def _compute_payment_ids_count(self):
        for record in self:
            record.payment_ids_count = len(record.payment_ids) if record.payment_ids else 0

    currency_id = fields.Many2one('res.currency', 
        related='company_id.currency_id',
        string='Currency',
        store=True)
    company_id = fields.Many2one("res.company", string="Company", default=_set_default_company, domain=_get_company_domain)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='State', readonly=True, default="draft", tracking=True)
    state_cancel = fields.Selection(related="state")

    ###############################################################
    ##   INHERITED METHOD
    ###############################################################

    @api.model
    def create(self, values):
        self.clear_caches()
        # values['name'] = self.env['ir.sequence'].get_sequence(self._name,'RDC/CA')
        values['name'] = 'New' if not values.get('name') else values.get('name')
        res = super(CashAdvance,self).create(values)
        if 'approval_info_ids' in values:
            res.updateTrxId()
        return res
    
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Anda hanya boleh menghapus Cash Advance dengan state Draft !")
        res = super(CashAdvance,self).unlink()
        return res

    ###############################################################
    ##   METHOD
    ###############################################################

    @api.constrains('employee_id','employee_id.address_home_id')
    def _constrains_employee_id(self):
        for record in self:
            if record.employee_id and not record.sudo().employee_id.address_home_id:
                raise ValidationError("Silahkan isi Kontak karyawan di Master Employee pada tab Informasi pribadi terlebih dahulu!")

    def create_payment(self):
        for record in self:
            payment_ids = []
            pay = self.env['account.payment'].create({
                'ref': record.name,
                
                'partner_id': record.sudo().employee_id.address_home_id.id,
                'currency_id': record.currency_id.id,
                'payment_type': 'outbound',
                'payment_mode': 'others',
                'criteria_type': 'cash_advance',
                'amount': record.total_amount,
                'date': record.date,
                'method_id': record.method_id.id,
                'journal_id': record.journal_id.id,
                'payment_line_ids': [
                    (0,0,{
                        'description': record.desc,
                        'account_id': record.account_id.id,
                        'amount': record.total_amount,
                    })
                ]
            })
            pay.action_post()
            payment_ids.append((4,pay.id))
            
            if payment_ids:
                record.payment_ids = payment_ids

            if record.parent_id and record.parent_id.bill_id and record.parent_id.bill_id.payment_state != 'paid':
                record.action_reconcile_bill(record.parent_id.bill_id)
                record.state = 'done'
                record.parent_id.state = 'done'


    def action_view_payments(self):
        for record in self:
            if record.payment_ids:
                if len(record.payment_ids) == 1:
                    # form_view_id = self.env.ref("account.view_account_payment_form").id
                    result = {
                        'name': 'Pembayaran',
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.payment',
                        'view_mode': 'form',
                        # 'view_type': 'form',
                        # 'views': [(form_view_id, 'form')],
                        'res_id': record.payment_ids[0].id,
                        'context': {
                            'create': False,
                        }
                    }
                    return result  
                else:
                    result = {
                        'name': 'Pembayaran',
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.payment',
                        'view_mode': 'tree,form',
                        # 'views': [
                        #     (self.env.ref('purchase.purchase_order_kpis_tree').id, 'tree'),
                        #     (self.env.ref('purchase.purchase_order_form').id, 'form')
                        # ],
                        'domain': [('id', 'in', self.payment_ids.ids)],
                        'context': {
                            'create': False,
                            'delete' : False
                        }
                    }
                    return result
            else:
                raise ValidationError("Cash Advance ini belum memiliki payment!")

    def action_create_bill(self):
        for record in self:
            okey = self._context.get('okey',False)
            real_desc = self._context.get('real_desc',record.desc)
            real_qty = self._context.get('real_qty',0)
            real_amount = self._context.get('real_amount',0)

            if not okey:
                context = {
                    'default_product_id':record.product_id.id,
                    'default_desc':record.desc,
                    'default_qty':record.qty,
                    'default_amount':record.amount,
                    'default_total_amount':record.total_amount,
                    'default_company_id':record.company_id.id,

                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_create_bill",
                    # 'default_function_parameter':record.,
                }
                return {
                    'type':'ir.actions.act_window',
                    'name':'Realisasi Cash Advance',
                    'res_model':'ca.realization.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_cash_advance.ca_realization_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                }
            
            record.sudo().write({
                'real_qty':real_qty,
                'real_amount':real_amount,
            })

            invoice_line_ids = []
            invoice_line_ids.append((0,0,{
                'product_id':record.product_id.id,
                'name': real_desc,
                'quantity': real_qty,
                'price_unit': real_amount
            }))
                
            values = {
                'partner_id': record.employee_id.address_home_id.id,
                'move_type': 'in_invoice',
                'company_id': record.company_id.id,
                'currency_id': record.currency_id.id,
                'date': record.date,
                'invoice_date': record.date,
                'ref':record.name,
                'invoice_origin':record.name,
                'invoice_line_ids': invoice_line_ids
            }
            bill = self.env['account.move'].create(values)

            if bill:
                # ganti akun receivablenya
                for line in bill.line_ids.filtered(lambda x: x.account_id.user_type_id.type == 'payable'):
                    line.account_id = record.account_id.id

                bill.action_post()
                # reconcile otomatis
                record.action_reconcile_bill(bill)

                record.bill_id = bill.id
                return record.action_view_bill()

    def action_reconcile_bill(self,bill):
        for record in self:
            if bill.invoice_outstanding_credits_debits_widget and json.loads(bill.invoice_outstanding_credits_debits_widget) and json.loads(bill.invoice_outstanding_credits_debits_widget).get('content'):
                    # raise UserError(str(json.loads(bill.invoice_outstanding_credits_debits_widget).get('content')))
                    for content in json.loads(bill.invoice_outstanding_credits_debits_widget).get('content'):
                        if content['journal_name'] == record.name:
                            bill.js_assign_outstanding_line(content['id'])

    def action_view_bill(self):
        for record in self:
            if record.bill_id:
                result = {
                    'name': "Bills",
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'views': [
                        # (self.env.ref('account.view_in_invoice_bill_tree').id, 'tree'),
                        (self.env.ref('account.view_move_form').id, 'form')
                    ],
                    'res_id': record.bill_id.id,
                    'context': {
                        'create': False,
                        'default_move_type': 'in_invoice'
                    }
                }
                return result
            else:
                raise ValidationError("Cash Advance ini belum memiliki Bill!")

    # action confirm
    def action_confirm(self):
        for record in self:
            if record.amount == 0:
                raise ValidationError("Anda harus mengisi amount terlebih dahulu !")

            record.sudo().write({
                'name': self.env['ir.sequence'].get_sequence(self._name,'RDC/CA') if record.name == 'New' else record.name,
                'state':'confirm'
            })
            record.sudo().send_schedule_actifity()
    
    # action approve
    # def action_approve(self):
    #     for record in self:
    #         record.sudo().write({
    #             'state':'approve'
    #         })
    #         # set done for all activity that refer to this user
    #         for activity in record.activity_ids:
    #             if activity.user_id.id == self.env.user.id:
    #                 activity.action_feedback(feedback="")
    
    #         # create payment
    #         record.create_payment()

    def action_approve(self):
        maxSeq = max(self.approval_info_ids.mapped('sequence'))
        lastApprove = False
        if self.approval_info_ids and self.state == 'confirm':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    i.sudo().write({
                        'is_approve': True,
                        'approve_user_id': self.env.user.id,
                        'approve_date': datetime.now(),
                    })
                    lastApprove = i.sequence == maxSeq
                    break

        if lastApprove:
            self.sudo().write({
                'state':'approve'
            })
            # create payment
            self.create_payment()

        for activity in self.activity_ids:
            activity.sudo().action_feedback(feedback="")

        if not lastApprove:
            self.sudo().send_schedule_actifity()

        return {}

    # action cancel
    def action_cancel(self):
        for record in self:
            if record.payment_ids or record.bill_id:
                raise ValidationError("anda tidak bisa cancel CA yang sudah dilakukan Payment atau dibuat Bill")
            record.sudo().write({
                'state':'cancel'
            })

    # action draft
    def action_draft(self):
        for record in self:
            record.sudo().write({
                'state':'draft'
            })
            record.cancel_approval()
    
    # action reject
    def action_reject(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_reject",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Confirmation Wizard',
                    'res_model':'confirm.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_input_message').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }

            record.sudo().write({
                'state':'draft',
            })
            # set done for all activity that refer to this user
            for activity in record.activity_ids:
                if activity.user_id.id == self.env.user.id:
                    activity.action_feedback(feedback=message)
            # set log message
            record.message_post(body="Cash Advance ini telah direject!\n\n\nAlasan : " + message)
            record.cancel_approval()

    # action set done
    def action_set_done(self):
        for record in self:
            if record.status_ca == 'kurang':
                if record.bill_id and record.bill_id.payment_state != 'paid':
                    raise ValidationError("Bill harus paid terlebih dahulu!")
                record.sudo().write({
                    'state':'done',
                })
            
    def action_create_another_ca(self):
        for record in self:
            if record.status_ca == 'kurang' and record.bill_id and record.bill_id.state == 'posted':
                ca2 = self.env['cash.advance'].create({
                    'name': str(record.name) + "-2",
                    'parent_id': record.id,

                    'employee_id': record.employee_id.id,
                    'loa_type': record.loa_type.id,

                    'product_id': record.product_id.id,
                    'desc': record.desc,
                    'qty': record.real_qty - record.qty if record.real_qty - record.qty > 1 else 1,
                    'amount': record.real_amount - record.amount,
                    # 'total_amount': record.real_total_amount - record.total_amount,

                    'date': datetime.now().date(),
                    'method_id': record.method_id.id,
                    'journal_id': record.journal_id.id,
                    'account_id': record.account_id.id,
                
                })
                ca2._onchange_loa_type()
                ca2._onchange_amount_total_approval_type()

                result = {
                    'name': "Cash Advance",
                    'type': 'ir.actions.act_window',
                    'res_model': 'cash.advance',
                    'view_mode': 'form',
                    # 'views': [
                    #     # (self.env.ref('account.view_in_invoice_bill_tree').id, 'tree'),
                    #     (self.env.ref('account.view_move_form').id, 'form')
                    # ],
                    'res_id': ca2.id,
                    'context': {
                        'create': False,
                    }
                }
                return result
            else:
                raise ValidationError("status Bill harus Posted terlebih dahulu!")


    def action_create_return_payment(self):
        for record in self:
            if record.status_ca == 'lebih':
                payment_ids = []
                pay = self.env['account.payment'].create({
                    'ref': record.name,
                    
                    'partner_id': record.sudo().employee_id.address_home_id.id,
                    'currency_id': record.currency_id.id,
                    'payment_type': 'inbound',
                    'payment_mode': 'others',
                    'criteria_type': 'cash_advance',
                    'amount': record.total_amount - record.real_total_amount,
                    'date': record.date,
                    'method_id': record.method_id.id,
                    'journal_id': record.journal_id.id,
                    'payment_line_ids': [
                        (0,0,{
                            'description': "return of %s" % record.name,
                            'account_id': record.account_id.id,
                            'amount': record.total_amount - record.real_total_amount,
                        })
                    ]
                })
                pay.action_post()
                payment_ids.append((4,pay.id))
                
                if payment_ids:
                    record.payment_ids = [(4,pay.id) for pay in record.payment_ids] + payment_ids

                    record.action_manual_reconcile(
                        payment1 = pay,
                        payment2 = record.payment_ids.filtered(lambda x: x.payment_type == 'outbound')[0]
                    )
                    
                    record.sudo().write({
                        'state':'done',
                    })

    def action_manual_reconcile(self,payment1,payment2):
        for rec in self:
            if rec.payment_ids: # ini menandakan bahwa sdh ada pembayaran kolombarium
                payment_move = self.env['account.move'].search([('payment_id','=',payment1.id)], limit=1)
                payment2_move = self.env['account.move'].search([('payment_id','=',payment2.id)], limit=1)
                to_recon = (payment_move + payment2_move).line_ids.filtered(lambda x: x.account_id.id == payment1.payment_line_ids[0].account_id.id \
                                                                                   and (x.matching_number == 'P' or x.matching_number == '' or x.matching_number == False) \
                                                                                    and x.reconciled == False) 
                to_recon.reconcile()
