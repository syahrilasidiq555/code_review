from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta, date


class CostSheet(models.Model):
    _name = 'cost.sheet'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Cost Sheet"

    # _sql_constraints = [
    #     ('check_unique_name', 'unique(name)', 
    #         'Name Already Exist.'), ]

    name = fields.Char('Name', tracking=True)


    date = fields.Date('Date', tracking=True)


    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    rel_is_rental_order = fields.Boolean(string='Is Rental Order', related='sale_order_id.is_rental_order', store=True)
    company_id = fields.Many2one(related='sale_order_id.company_id', store=True)
    
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string='Almarhum', store=True)
    penanggungjawab_id = fields.Many2one(related='sale_order_id.penanggungjawab_id', store=True)

    currency_id = fields.Many2one('res.currency', 
        related='sale_order_id.currency_id',
        string='Currency',
        store=True)
    
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approved','Approved'),
        ('done','Done'),
        ('cancel', 'Canceled')],
        default='draft',
        string='State', tracking=True)
        
    state_cancel = fields.Selection(related='state')

    confirm_uid = fields.Many2one('res.users', string='Confirmed by', tracking=True)
    confirm_date = fields.Datetime('Confirmed on', tracking=True)
    approved_uid = fields.Many2one('res.users', string='Approved by', tracking=True)
    approved_date = fields.Datetime('Approved on', tracking=True)


    cost_sheet_line = fields.One2many('cost.sheet.line', 'cost_sheet_id', string='Cost Sheet Line')

    po_ids = fields.Many2many('purchase.order', 'po_id', 'cost_sheet_id', string='Purchase Order List')
    po_ids_count = fields.Integer(compute='_compute_po_ids_count', string='Purchase Order List Count')
    bill_ids = fields.Many2many('account.move', 'move_id', 'cost_sheet_id', string='Bills List', compute='_compute_bill_ids_count', store=True)
    bill_ids_count = fields.Integer(compute='_compute_bill_ids_count', string='Bills List Count')
    
    @api.depends('po_ids','po_ids.invoice_ids','cost_sheet_line','cost_sheet_line.actual_budget','cost_sheet_line.budget_cost')
    def _compute_bill_ids_count(self):
        for record in self:
            record.bill_ids_count = 0
            record.bill_ids = None
            bill_ids = self.env['account.move'].search([
                ('move_type','=','in_invoice'),
                ('cost_sheet_id','=',record.id),
            ])
            if bill_ids:
                record.bill_ids = bill_ids
                record.bill_ids_count = len(bill_ids)

    @api.depends('po_ids')
    def _compute_po_ids_count(self):
        for record in self:
            record.po_ids_count = 0
            if record.po_ids:
                record.po_ids_count = len(record.po_ids)

    amount_actual_sales = fields.Monetary(compute='_compute_actual_sales', string='Sales Subtotal', digits='Product Price', default=0.0, store=True)
    amount_actual_bill = fields.Monetary(compute='_compute_actual_sales', string='Bill Subtotal', digits='Product Price', default=0.0, store=True)
    amount_actual_margin = fields.Monetary(compute='_compute_actual_sales', string='Margin Subtotal', digits='Product Price', default=0.0, store=True)
    actual_margin_percentage = fields.Float(compute='_compute_actual_sales', string='Percentage', store=True)
    
    @api.depends('cost_sheet_line', 'cost_sheet_line.product_id', 'cost_sheet_line.actual_sales', 'cost_sheet_line.actual_budget', 'cost_sheet_line.budget_margin', 'sale_order_id','sale_order_id.tax_totals_json')
    def _compute_actual_sales(self):
        for record in self:
            amount_actual_sales = 0
            amount_actual_bill = 0
            amount_actual_margin = 0

            for line in record.cost_sheet_line:
                amount_actual_sales += line.actual_sales
                amount_actual_bill += line.actual_budget
                amount_actual_margin += line.budget_margin
            
            record.amount_actual_sales = amount_actual_sales
            record.amount_actual_bill = amount_actual_bill
            record.amount_actual_margin = amount_actual_margin
            record.actual_margin_percentage = round(((amount_actual_sales - amount_actual_bill) / amount_actual_sales) * 100, 2) if record.amount_actual_sales else 0
                


    is_all_po_bill_created = fields.Boolean(compute='_compute_is_all_po_bill_created', string='Is all PO & Bill Created?')
    
    @api.depends('po_ids','po_ids.invoice_ids','bill_ids')
    def _compute_is_all_po_bill_created(self):
        for record in self:
            is_all_po_bill_created = True

            for line in record.cost_sheet_line:
                if line.is_konsinyasi and line.vendor_id and not line.bill_line_id:
                    is_all_po_bill_created = False
                    break
                elif not line.is_konsinyasi and line.vendor_id and not line.po_line_id:
                    is_all_po_bill_created = False
                    break

            record.is_all_po_bill_created = is_all_po_bill_created

    ###############################################################
    ##   INHERITED METHOD
    ###############################################################

    @api.model
    def create(self, values):
        self.clear_caches()
        values['name'] = self.env['ir.sequence'].get_sequence(self._name,'RDC/CS')
        res = super(CostSheet,self).create(values)
        res.set_vendor_list()
        return res
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("Anda hanya bisa delete data dengan state Draft!")
            
            if record.bill_ids or record.po_ids:
                raise UserError("Anda tidak bisa delete data yang sudah mempunyai Bill atau PO")
        return super(CostSheet, self).unlink()
    

    ###############################################################
    ##   METHOD
    ###############################################################

    # automatically set vendor
    def set_vendor_list(self):
        for record in self:
            for line in record.cost_sheet_line.filtered(lambda x: not x.vendor_id):
                # disesuaikan nanti saat sudah ada fitur rolling vendor
                line.vendor_id = None
                if line.sale_order_line_id.default_vendor_id:
                    line.vendor_id = line.sale_order_line_id.default_vendor_id.id
                    line.budget_cost_unit = line.sale_order_line_id.price_unit
                elif line.product_id.seller_ids:
                    for seller in line.product_id.seller_ids:
                        line.vendor_id = seller.name.id
                        line.budget_cost_unit = seller.price
                        break
                    line.product_id.product_tmpl_id.roll_vendor(line.vendor_id.id)
                
            # hapus vendor_id kalau qtynya 0 & rollback
            for line in record.cost_sheet_line.filtered(lambda x: x.qty == 0 and x.vendor_id):
                # line.product_id.product_tmpl_id.roll_vendor_rollback(line.vendor_id.id)
                line.vendor_id = None
    
    # fungsi validasi vendor dan budget
    def validate_vendor(self):
        for record in self:
            for line in record.cost_sheet_line:
                if line.is_konsinyasi and not line.vendor_id:
                    raise UserError("You must pick vendor for `Konsinyasi` Product!")
                if line.vendor_id and line.budget_cost_unit == 0:
                    raise UserError("You must fill Budget field if you pick Vendor\n\nProduct : {product_name}".format(
                        product_name=line.name
                    ))

    # tombol confirm (works for multi id)
    def action_confirm(self):
        for record in self:
            record.validate_vendor()

            okey = self._context.get('okey',False)
            recipent_user_id = self._context.get('recipent_user_id',False)

            if not okey:
                context = {
                    'default_message': "Please fill the recipent field if you want to send email reminder",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_confirm",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Confirmation Wizard',
                    'res_model':'confirm.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }

            record.write({
                'state':'confirm',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
                })
            
            # create schedule activity
            if recipent_user_id:
                self.env['mail.activity'].create({
                    'display_name': 'dont forget to approve this cost sheet as fast as possible',
                    'summary': 'Please approve this Cost Sheet',
                    'date_deadline': datetime.now(),
                    'user_id': recipent_user_id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('custom_sale_order.model_cost_sheet').id,
                    'activity_type_id': 4
                })

    # tombol approve (works for multi id)
    def action_approve(self):
        for record in self:
            record.write({
                'state':'approved',
                'approved_uid': self.env.user.id,
                'approved_date': datetime.now(),
            })
            # set done for all activity that refer to this user
            for activity in record.activity_ids:
                if activity.user_id.id == self.env.user.id:
                    activity.action_feedback(feedback="")
    
    # tombol reject (works for multi id)
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

            record.write({
                'state':'draft',
            })
            # set done for all activity that refer to this user
            for activity in record.activity_ids:
                if activity.user_id.id == self.env.user.id:
                    activity.action_feedback(feedback=message)
            # set log message
            record.message_post(body="This Cost Sheet is Rejected!\n\nRejected Reason : " + message)
    
    # tombol cancel (works for multi id)
    def action_cancel(self):
        for record in self:
            record.write({'state':'cancel'})

    # tombol draft (works for multi id)
    def action_draft(self):
        for record in self:
            record.write({'state':'draft'})

    # tombol view sales order
    def action_view_so(self):
        for record in self:
            if record.sale_order_id:
                form_view_id = self.env.ref("sale.view_order_form").id
                name = 'Sale Order'
                if record.sale_order_id.is_rental_order:
                    form_view_id = self.env.ref("sale_renting.rental_order_primary_form_view").id
                    name = 'Rental Order'
        
                result = {
                    'name': _(name),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    # 'view_type': 'form',
                    'views': [(form_view_id, 'form')],
                    'res_id': self.sale_order_id.id,
                    'context': {'create': False},
                }
                return result  
            else:
                raise UserError("Sales Order not available")
            
    # tombol view rental schedule
    def action_view_rental_schedule(self):
        for record in self:
            if record.sale_order_id.is_rental_order:
                return record.sale_order_id.action_view_rental_schedule()
            else:
                raise UserError("Rental Order not available")

    # tombol create PO
    # create PO per vendor
    def action_create_po(self):
        for record in self:
            po_ids = []

            # get vendor list
            vendor_list = []
            for line in record.cost_sheet_line.filtered(lambda x : x.vendor_id and not x.is_konsinyasi and not x.po_line_id):
                if line.vendor_id.id not in vendor_list:
                    vendor_list.append(line.vendor_id.id)

            # if len(vendor_list) == 0:
            #     raise UserError("You must fill vendor column before create Purchase Order !")
            
            # create PO
            for vendor_id in vendor_list:
                order_line = []
                for line in record.cost_sheet_line.filtered(lambda x : x.vendor_id and not x.is_konsinyasi and not x.po_line_id):
                    if line.vendor_id.id == vendor_id:
                        order_line.append((0,0,{
                            'cost_sheet_line_id':line.id,
                            'product_id':line.product_id.id,
                            'name': line.name,
                            # 'product_qty': 1,
                            'product_qty': line.qty,
                            'price_unit': line.budget_cost_unit
                        }))
                
                values = {
                    'cost_sheet_id': record.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    # 'date_order': record.date,
                    'date_order': record.sale_order_id.date_order,
                    'partner_id': vendor_id,
                    'loa_type': None,
                    # 'picking_type_id':
                    'order_line': order_line
                }
                po = self.env['purchase.order'].sudo().create(values)
                # po._onchange_amount_total_approval_type()
                # po._onchange_loa_type()
                po_ids.append((4, po.id))

            record.po_ids = po_ids
    
    # create PO per item
    def action_create_po(self):
        for record in self:
            po_ids = []
            
            # create PO
            for line in record.cost_sheet_line.filtered(lambda x : x.vendor_id and not x.is_konsinyasi and not x.po_line_id):
                values = {
                    'cost_sheet_id': record.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    # 'date_order': record.date,
                    'date_order': record.sale_order_id.date_order,
                    'partner_id': line.vendor_id.id,
                    'loa_type': None,
                    # 'picking_type_id':
                    'order_line': [(0,0,{
                        'cost_sheet_line_id':line.id,
                        'product_id':line.product_id.id,
                        'name': line.name,
                        # 'product_qty': 1,
                        'product_qty': line.qty,
                        'price_unit': line.budget_cost_unit
                    })]
                }
                po = self.env['purchase.order'].sudo().create(values)
                # po._onchange_amount_total_approval_type()
                # po._onchange_loa_type()
                po_ids.append((4, po.id))

            record.po_ids = po_ids

    # tombol view PO
    def action_view_po_list(self):
        result = {
            'name': _("Purchase Order"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('purchase.purchase_order_kpis_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_form').id, 'form')
            ],
            'domain': [('id', 'in', self.po_ids.ids)],
            'context': {
                'create': False,
            }
        }
        return result

    # tombol create vendor bills
    def action_create_vendor_bills(self):
        for record in self:
            # validasi
            # if record.bill_ids:
            #     raise UserError("Cannot Create More Bills")

            bill_ids = []

            # get vendor list
            vendor_list = []
            for line in record.cost_sheet_line.filtered(lambda x : x.vendor_id and x.is_konsinyasi and not x.bill_line_id):
                if line.vendor_id.id not in vendor_list:
                    vendor_list.append(line.vendor_id.id)


            # validasi apakah ada vendor list
            # if len(vendor_list) == 0:
            #     raise UserError("You must fill vendor column before create vendor bills !")

            for vendor_id in vendor_list:
                invoice_line_ids = []
                for line in record.cost_sheet_line.filtered(lambda x : x.vendor_id and x.is_konsinyasi and not x.bill_line_id):
                    if line.vendor_id.id == vendor_id:
                        invoice_line_ids.append((0,0,{
                            'cost_sheet_line_id':line.id,
                            'product_id':line.product_id.id,
                            'name': line.name,
                            'quantity': 1,
                            'price_unit': line.budget_cost
                        }))
                
                values = {
                    'move_type': 'in_invoice',
                    'is_konsinyasi_bill': True,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    'date': record.date,
                    'invoice_date': record.date,
                    'partner_id': vendor_id,
                    'invoice_origin':record.name,
                    'invoice_line_ids': invoice_line_ids
                }
                bill = self.env['account.move'].sudo().create(values)
                bill_ids.append((4, bill.id))

            # record.bill_ids = bill_ids
            # return record.action_view_bills()

    # tombol view bills
    def action_view_bills(self):
        result = {
            'name': _("Vendor Bills"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_in_invoice_bill_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form')
            ],
            'domain': [('id', 'in', self.bill_ids.ids)],
            'context': {
                'create': False,
                'default_move_type': 'in_invoice'
            }
        }
        return result
    
    # tombol create po & bills
    def action_create_po_and_bills(self):
        for record in self:
            record.action_create_po()
            record.action_create_vendor_bills()
            
            for line in record.cost_sheet_line:
                line._compute_po_line()
                line._compute_bill_line()
            record._compute_is_all_po_bill_created()

class CostSheetLine(models.Model):
    _name = 'cost.sheet.line'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Cost Sheet Line"

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet', ondelete='cascade', required=True, index=True, copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', related='cost_sheet_id.currency_id', depends=['cost_sheet_id.currency_id'], store=True)


    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    sale_order_id = fields.Many2one('sale.order', related='sale_order_line_id.order_id',string='Sale Order')

    is_konsinyasi = fields.Boolean(compute='_compute_is_konsinyasi', string='is Konsinyasi', store=True)
    
    bill_line_id = fields.Many2one('account.move.line', compute="_compute_bill_line", string='Bill Line', store=True)
    bill_id = fields.Many2one('account.move', related="bill_line_id.move_id", string='bill')
    
    @api.depends('cost_sheet_id','cost_sheet_id.bill_ids','cost_sheet_id.po_ids','cost_sheet_id.po_ids.invoice_ids')
    def _compute_bill_line(self):
        for record in self:
            bill_line = self.env['account.move.line'].search([('cost_sheet_line_id','=',record.id)], limit=1)
            record.bill_line_id = bill_line.id if bill_line else None

    po_line_id = fields.Many2one('purchase.order.line', compute="_compute_po_line", string='Purchase Order Line', store=True)
    po_id = fields.Many2one('purchase.order', related="po_line_id.order_id", string="Purchase Order")

    @api.depends('cost_sheet_id','cost_sheet_id.po_ids','cost_sheet_id.po_ids.invoice_ids')
    def _compute_po_line(self):
        for record in self:
            po_line = self.env['purchase.order.line'].search([('cost_sheet_line_id','=',record.id)], limit=1)
            record.po_line_id = po_line.id if po_line else None

    @api.depends('sale_order_line_id','sale_order_line_id.product_warehouse_id','sale_order_line_id.product_id')
    def _compute_is_konsinyasi(self):
        for record in self:
            record.is_konsinyasi = False
            if record.sale_order_line_id.product_warehouse_id.id == int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')):
                record.is_konsinyasi = True

    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        change_default=True, 
        ondelete='restrict')
    name = fields.Text(string='Description')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.name = record.product_id.name

    vendor_id = fields.Many2one('res.partner', string='Vendor')

    budget_cost_unit = fields.Monetary('Purchase Price Unit', digits='Product Price', default=0.0, store=True)
    budget_cost = fields.Monetary(compute='_compute_actual_sales', string='Purchase Subtotal', digits='Product Price', default=0.0, store=True)

    qty = fields.Integer(compute='_compute_actual_sales', string='Actual Sales Quantity', store=True)
    actual_sales_unit = fields.Monetary(compute='_compute_actual_sales', string='Actual Sales Price Unit', digits='Product Price', default=0.0, store=True)
    actual_sales = fields.Monetary(compute='_compute_actual_sales', string='Actual Sales Subtotal', store=True)
    @api.depends('budget_cost_unit', 'sale_order_line_id', 'sale_order_line_id.price_subtotal', 'sale_order_line_id.name', 'sale_order_line_id.product_id', 'sale_order_id','sale_order_id.tax_totals_json')
    def _compute_actual_sales(self):
        for record in self:
            record.actual_sales = 0
            record.qty = 0
            record.actual_sales_unit = 0
            record.budget_cost = 0
            if record.sale_order_line_id:
                record.actual_sales = record.sale_order_line_id.price_subtotal
                record.qty = record.sale_order_line_id.product_uom_qty
                record.actual_sales_unit = record.sale_order_line_id.price_unit
                record.product_id = record.sale_order_line_id.product_id.id
                record.name = record.sale_order_line_id.name
                record.budget_cost = record.qty * record.budget_cost_unit
            elif not record.sale_order_line_id:
                record.unlink()
                

    actual_budget = fields.Monetary(compute='_compute_actual_budget', string='Bill Subtotal', store=True)
    @api.depends('cost_sheet_id','cost_sheet_id.bill_ids','cost_sheet_id.bill_ids.invoice_line_ids','cost_sheet_id.bill_ids.invoice_line_ids.price_subtotal','cost_sheet_id.po_ids','cost_sheet_id.po_ids.invoice_ids','cost_sheet_id.po_ids.invoice_ids.invoice_line_ids','cost_sheet_id.po_ids.invoice_ids.invoice_line_ids.price_subtotal')
    def _compute_actual_budget(self):
        for record in self:
            record.actual_budget = 0
            bill_lines = self.env['account.move.line'].search([('cost_sheet_line_id','=',record.id)])
            actual_budget = 0
            for line in bill_lines:
                actual_budget += line.price_subtotal
            record.actual_budget = actual_budget


    budget_margin = fields.Monetary(compute='_compute_budget', string='Margin Budget', digits='Product Price', default=0.0, store=True)
    budget_percentage = fields.Float(compute='_compute_budget', string='%', digits='Product Price', default=0.0, store=True)
    @api.depends('actual_budget', 'actual_sales')
    def _compute_budget(self):
        for record in self:
            record.budget_margin = 0
            record.budget_percentage = 0

            record.budget_margin = record.actual_sales - record.actual_budget
            if record.actual_sales > 0:                
                record.budget_percentage = round(((record.actual_sales - record.actual_budget) / record.actual_sales) * 100)

    # PRINT2AN
    def print_pemesanan_vendor(self):
        return self.env.ref('custom_sale_order.action_report_pemesanan_vendor_rdc').report_action(self)
    
    ###############################################################
    ##   INHERITED METHOD
    ###############################################################

    @api.model
    def create(self, values):
        res = super(CostSheetLine,self).create(values)
        if res.cost_sheet_id and not res.vendor_id:
            res.cost_sheet_id.set_vendor_list()
        return res

    def unlink(self):
        for record in self:
            # kalau ada vendornya, rollback dlu sebelum di delete
            if record.vendor_id:
                record.product_id.product_tmpl_id.roll_vendor_rollback(record.vendor_id.id)
        return super(CostSheetLine, self).unlink()

    ###############################################################
    ##   METHOD
    ############################################################### 

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self,vendor_id=None):
        for record in self:
            # sesuaikan harga purchase price unit
            record.budget_cost_unit = 0
            if record.vendor_id:
                for seller in record.product_id.seller_ids:
                    if seller.name.id == record.vendor_id.id:
                        record.budget_cost_unit = seller.price
            elif not record.vendor_id:
                # kalau vendor_id dikosongkan, maka rollback vendornya
                vendor = vendor_id if vendor_id else record._origin.vendor_id
                record.product_id.product_tmpl_id.roll_vendor_rollback(vendor.id)

    def action_change_vendor(self):
        for record in self:
            result = {
                'name': _('Choose Vendor'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('custom_sale_order.choose_partner_wizard_view').id, 
                'res_model': 'choose.partner.wizard', 
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_cost_sheet_id': record.cost_sheet_id.id,
                    'default_cost_sheet_line_id': record.id,
                }
            }
            return result  
            