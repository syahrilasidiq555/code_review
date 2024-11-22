from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import OrderedSet, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

from datetime import datetime
from collections import Counter, defaultdict

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # UNTUK APPROVAL
    state = fields.Selection(selection_add=[
        ('assigned',),
        ('to approve','To Approve'),
        ('rejected','Rejected'), 
        ('done',), 
    ])

    # @api.model
    # def _default_loa(self):
    #     dt = self.env['level.approval'].sudo().search([('model_id.model', '=', self._name)], order="id asc", limit=1)
    #     return dt.id if dt else False

    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'stock.picking')])
    approval_info_ids = fields.Many2many(
            'approval.info',
            'approval_info_picking_rel',
            'picking_id',
            'approval_id', 
            string='Approval Information', store=True)
    next_approve_user_id = fields.Many2one('res.users', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    # is_amount = fields.Boolean(string="Range Amount", store=True)
    # from_amount = fields.Float(string='From Amount', store=True)
    # to_amount = fields.Float(string='To Amount', store=True)

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
            if rec.approval_info_ids and rec.state in ['to approve','draft','waiting','confirmed','assigned']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        rec.next_approve_user_id = i.user_id.id
                        break


    @api.onchange('loa_type','picking_type_id')
    def _onchange_loa_type(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.loa_type:
                # if rec.loa_type.is_amount:
                #     if rec.amount_total >= rec.loa_type.from_amount and rec.amount_total <= rec.loa_type.to_amount:
                #         rec.is_amount = rec.loa_type.is_amount
                #         rec.from_amount = rec.loa_type.from_amount
                #         rec.to_amount = rec.loa_type.to_amount
                #     else:
                #         raise ValidationError("Total Order tidak sesuai dengan range amount pada Approval Type")
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


    # @api.onchange('amount_total','order_line','order_line.price_subtotal')
    # def _onchange_amount_total_approval_type(self):
    #     for record in self:
    #         if record.amount_total:
    #             dtApprvl = self.env['level.approval'].search([
    #                 ('model_id.model', '=', self._name),
    #                 ('from_amount','<=',record.amount_total),
    #                 ('to_amount','>=',record.amount_total)
    #             ], limit=1)
    #             if dtApprvl:
    #                 self.loa_type = dtApprvl.id
        

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


    @api.model_create_multi
    def create(self, vals_list):
        res =  super().create(vals_list)
        for record in res:
            record._onchange_loa_type()
        return res
    
    def validate_lot_picking(self):
        for record in self:
            move_line_ids = []
            ml_ids_tracked_without_lot = OrderedSet()
            ml_ids_to_delete = OrderedSet()
            ml_ids_to_create_lot = OrderedSet()
            ml_ids_to_check = defaultdict(OrderedSet)
            for move in record.move_ids:
                move_line_ids += [x.id for x in move.move_line_ids]
            # raise UserError(str(record.move_ids.read()))

            for ml in self.env['stock.move.line'].sudo().browse(move_line_ids):
                qty_done_float_compared = float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done_float_compared > 0:
                    if ml.product_id.tracking == 'none':
                        continue
                    picking_type_id = ml.move_id.picking_type_id
                    if not picking_type_id and not ml.is_inventory and not ml.lot_id:
                        ml_ids_tracked_without_lot.add(ml.id)
                        continue
                    if not picking_type_id or ml.lot_id or (not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots):
                        # If the user disabled both `use_create_lots` and `use_existing_lots`
                        # checkboxes on the picking type, he's allowed to enter tracked
                        # products without a `lot_id`.
                        continue
                    if picking_type_id.use_create_lots:
                        ml_ids_to_check[(ml.product_id, ml.company_id)].add(ml.id)
                    else:
                        ml_ids_tracked_without_lot.add(ml.id)

                elif qty_done_float_compared < 0:
                    raise UserError(_('No negative quantities allowed'))
                elif not ml.is_inventory:
                    ml_ids_to_delete.add(ml.id)

            for (product, company), mls in ml_ids_to_check.items():
                mls = self.env['stock.move.line'].browse(mls)
                lots = self.env['stock.lot'].search([
                    ('company_id', '=', company.id),
                    ('product_id', '=', product.id),
                    ('name', 'in', mls.mapped('lot_name')),
                ])
                lots = {lot.name: lot for lot in lots}
                for ml in mls:
                    lot = lots.get(ml.lot_name)
                    if lot:
                        ml.lot_id = lot.id
                    elif ml.lot_name:
                        ml_ids_to_create_lot.add(ml.id)
                    else:
                        ml_ids_tracked_without_lot.add(ml.id)


            if ml_ids_tracked_without_lot:
                mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
                raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
                                '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))

    def validate_serial_number(self):
        for record in self:
            for move in record.move_ids.filtered(lambda x:x.product_id.tracking == 'serial'):
                # lot_names = []
                message = "The serial number has already been assigned: "
                error = False
                for ml in move.move_line_ids:
                    # lot_names.append(ml.lot_name)
                    quants = self.env['stock.quant'].sudo().search([
                        ('location_id.usage','!=','inventory'),
                        ('lot_id','!=',False),
                        ('lot_id.name','=',ml.lot_name),
                    ])
                    if quants:
                        error = True
                        message += f'\n Product: {quants[0].product_id.display_name}, Serial Number: {quants[0].lot_id.name}'
                if error:
                    raise UserError(message)

    ###############################################################
    ##   BUTTON ACTION
    ###############################################################     
    def button_validate(self):
        for record in self:
            force_validate = self._context.get('force_validate', False)
            if record.loa_type and not force_validate:
                record._sanity_check()
                record.validate_lot_picking()
                record.validate_serial_number()
                record.write({'state' : 'to approve'})
                record.send_schedule_activity()
            else:
                return super(StockPicking, self).button_validate()



    def button_reject(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
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

            # set is approve to false
            for info in record.approval_info_ids.filtered(lambda x: x.is_approve):
                info.is_approve = False
            
            record.sudo().write({
                'state': 'rejected'
            })
            record._onchange_loa_type()
    
    def button_draft(self):
        for record in self:
            if record.state == 'rejected':
                record.sudo().write({'state':'draft'})

    def button_multi_reject(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to approve'):
            record.with_context({'okey':True}).button_reject()

    def button_multi_approve(self):
        for record in self.filtered(lambda x: x.is_user_approve_now and x.state == 'to approve'):
            record.button_approve()
    
    def button_approve(self, force=False):
        # res = super(StockPicking, self).button_approve()
        for record in self:
            # record.sudo().write({'state':'to approve'})
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
                # record.write({'state': 'purchase'})
                res = super(StockPicking, self).with_context(force_validate=True).button_validate()
                # return res

            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            if not lastApprove:
                record.send_schedule_activity()