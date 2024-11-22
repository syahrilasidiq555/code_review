from odoo import models, fields, api

class stockPicking(models.Model):
    _inherit = 'stock.picking'

    # inherited fields
    date_done = fields.Datetime(readonly=False, required=True)

    # document
    vendor_surat_jalan = fields.Binary(string='Surat Jalan Vendor', attachment=True, store=True, tracking=True)
    vendor_surat_jalan_filename = fields.Char(string='Surat Jalan Vendor', tracking=True)

    # override function
    def _action_done(self):
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))

        # sisi customnya dari sini
        if not self.date_done:
            self.write({'date_done': fields.Datetime.now(), 'priority': '0'})
        else:
            self.write({'priority': '0'})
        # sampai sini

        # if incoming moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True
    
    @api.model
    def create(self, vals):
        res = super(stockPicking, self).create(vals)
        return res