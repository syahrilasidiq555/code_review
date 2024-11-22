from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.model
    def _default_loa(self):
        dt = self.env['level.approval'].search([('model_id.model', '=', 'purchase.request')], order="id asc", limit=1)
        return dt.id if dt else False

    # tipe permintaan
    request_type =  fields.Selection(
        string='Request Type', 
        selection=[('purchase', 'Pembelian'), ('delivery', 'Kebutuhan Internal')],
        default='purchase', store=True)
    picking_id = fields.Many2one('stock.picking', string='Delivery')

    @api.onchange('request_type')
    def onchange_request_type(self):
        if self.request_type == 'purchase':
            domain = {
                'domain': {
                    'picking_type_id': [
                        ('code', '=', 'incoming')
                    ]
                }
            }

            dt = self.env['stock.picking.type'].search([("code", "=", "incoming")], limit=1)
            if dt:
                self.picking_type_id = dt.id
        elif self.request_type == 'delivery':
            self.picking_type_id = False
            domain = {
                'domain': {
                    'picking_type_id': [
                        ('code', '=', 'outgoing'),
                        ('name','=','Internal Use')
                    ]
                }
            }

            self.loa_type = False

            dt = self.env['stock.picking.type'].search([("code", "=", "outgoing"), ('name','=','Internal Use')], limit=1)
            if dt:
                self.picking_type_id = dt.id
        return domain
    
    def create_delivery(self):
        # cari operation type yang jenisnya delivery / out
        operation_type = self.picking_type_id 
        operation_type_id = operation_type.id

        cust_location = self.env.ref('stock.stock_location_customers')
        location_id = operation_type.default_location_src_id.id
        if operation_type.default_location_dest_id.id:
            cust_location_id = operation_type.default_location_dest_id.id
        else:
            cust_location_id = cust_location.id

        # set line items
        move_ids = []
        for item in self.line_ids:
            move_ids.append((0,0,{
                'product_id': item.product_id.id,
                'name':item.name,
                'product_uom_qty': item.product_qty,
                'product_uom':item.product_id.uom_id.id,
                'location_id': location_id,
                'location_dest_id':cust_location_id,
                'purchase_request_line_id': item.id,
            }))
    
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': operation_type_id,
            'location_id': location_id,
            'location_dest_id': cust_location_id,
            'partner_id': False,
            'scheduled_date': self.date_start, #datetime.now(),
            'origin': self.name,
            'move_type': 'one', # when all products are ready
            'company_id': self.company_id.id,

            'move_ids_without_package':move_ids if move_ids else False,
        })
        picking.action_confirm()
        self.write({'picking_id':picking.id})

        result = {
            'name': "Delivery",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }
        return result
    
    def action_view_picking_delivery(self):
        result = {
            'name': "Delivery",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
        }
        return result

    # Kebutuhan Approval
    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'purchase.request')], default=_default_loa)
    approval_info_ids = fields.Many2many('approval.info','purchase_request_approval_line','purchase_request_id','approval_id', 
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

    @api.onchange('loa_type')
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
                        'approver_sign': False,
                    }]
                    app_inf.append(tmp)
            rec.approval_info_ids = app_inf

    @api.depends('estimated_cost','line_ids')
    @api.onchange('estimated_cost','line_ids')
    def _onchange_amount_total_approval_type(self):
        if self.estimated_cost:
            dtApprvl = self.env['level.approval'].search([('model_id.model', '=', 'purchase.request'),('from_amount','<=',self.estimated_cost),('to_amount','>=',self.estimated_cost)], limit=1)
            if dtApprvl and self.request_type != 'delivery':
                self.loa_type = dtApprvl.id

    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_id = False
            if rec.approval_info_ids and rec.state in ['to_approve','draft','sent']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break

    def send_schedule_actifity(self):
        todos = {
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'purchase.request')]).id,
            'user_id': self.next_approve_user_id.id,
            'summary': 'Request Approval',
            'note': 'Hi. Please approve this order',
            'activity_type_id': 4,
            'date_deadline': datetime.now(),
        }
        self.env['mail.activity'].sudo().create(todos)

    def button_to_approve(self):
        self._onchange_loa_type()
        self._compute_next_approval()
        self.sudo().to_approve_allowed_check()
        if self.loa_type:
            self.sudo().write({'state': 'to_approve'})
            self.sudo().send_schedule_actifity()
        return 
    
    def button_rejected(self):
        self.sudo().mapped("line_ids").do_cancel()
        return self.sudo().write({"state": "rejected"})
    
    def button_approved(self):
        maxSeq = max(self.approval_info_ids.mapped('sequence'))
        lastApprove = False
        if self.approval_info_ids and self.state == 'to_approve':
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
            self.sudo().write({'state': 'approved'})

        for activity in self.activity_ids:
            activity.sudo().action_feedback(feedback="")

        if not lastApprove:
            self.sudo().send_schedule_actifity()

        return {}
    
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

    def button_rejected(self):
        self.mapped("line_ids").do_cancel()
        self.cancel_approval()
        return self.write({"state": "rejected"})
    
    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        self.cancel_approval()
        return self.write({"state": "draft"})
    
    @api.depends()
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "draft" and rec.request_type == 'purchase' and any(
                not line.cancelled and line.product_qty for line in rec.line_ids
            ) and self.env.user.id == rec.requested_by.id

    @api.model
    def create(self, vals):
        res = super(PurchaseRequest, self).create(vals)
        if res:
            if res.request_type == 'delivery':
                res.write({'state':'approved'})
                
            if 'approval_info_ids' in vals:
                res.updateTrxId()
        return res
    
    def write(self, vals):
        if 'request_type' in vals:
            if vals['request_type'] == 'delivery':
                vals['state'] = 'approved'  
        res = super(PurchaseRequest, self).write(vals)
        return res
    
    
class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    date_required = fields.Date(
        default=False,
        required=False,
        related="request_id.date_start", store=True
    )

    stock_move_line_id = fields.Many2one('stock.move', string="Stock Move", compute="_compute_line_id")
    @api.depends('request_id.picking_id')
    def _compute_line_id(self):
        for rec in self:
            dt = self.env['stock.move'].search([('purchase_request_line_id','=',rec.id)])
            rec.stock_move_line_id = dt[0].id if dt else False
    
    @api.onchange("product_id", "product_qty")
    def onchange_product_id_tambahan(self):
        if self.product_id:
            self.estimated_cost = self.product_id.standard_price * (self.product_qty * self.product_uom_id.ratio)