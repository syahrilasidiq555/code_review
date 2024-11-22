from odoo import models, fields, api, tools, _


class ReportPurchaseOrderCustom(models.Model):
    _name = "report.purchase.order.custom"
    _description = "Report Purchase Order"
    _auto = False
    _order = "date_order desc, id"
    _rec_name = "purchase_line_id"

    # purchase
    purchase_id = fields.Many2one('purchase.order', string='PO. No')
    date_order = fields.Datetime(string='PO. Date')
    date_planned = fields.Datetime(string='PO. Expected Arrival')
    partner_id = fields.Many2one('res.partner',string='Vendor')
    purchase_state = fields.Selection(related="purchase_id.state")

    project_id = fields.Many2one('project.project',string='Project')
    end_customer_id = fields.Many2one('res.partner', string='End Customer')

    # purchase line
    purchase_line_id = fields.Many2one('purchase.order.line', string='PO Line')
    product_id = fields.Many2one('product.product', string='Product')
    default_code = fields.Char(string='Internal Ref')
    pol_description = fields.Text(string='Product Description')
    product_qty = fields.Float(string='Quantity')
    qty_received = fields.Float(related="purchase_line_id.qty_received", string='Qty Received')

    receive_status = fields.Selection([
        ('no', 'No Receive'),
        ('partial', 'Partial'),
        ('full', 'Full Received'),
    ], compute='_compute_receive_status', string='Receive Stetaus')
    
    @api.depends('purchase_line_id.qty_received','product_qty','qty_received')
    def _compute_receive_status(self):
        for record in self:
            record.receive_status = 'no'
            if record.product_qty and record.qty_received:
                if record.product_qty == record.qty_received:
                    record.receive_status = 'full'
                elif record.qty_received < record.product_qty:
                    record.receive_status = 'partial'

    # stock move
    move_ids = fields.One2many(related="purchase_line_id.move_ids", string='Stock Receipt(s)')
    move_ids_name = fields.Text(compute='_compute_move_ids_name', string='Stock Receipt(s)',
        search="_search_move_ids_name")
    def _search_move_ids_name(self, operator, value):
        if operator == '=':
            operator = 'ilike'
        return [('move_ids.reference', operator, value)]
    
    move_ids_date = fields.Datetime(compute='_compute_move_ids_name', string='Receipt Date')

    @api.depends('purchase_id','purchase_line_id','purchase_line_id.move_ids','move_ids')
    def _compute_move_ids_name(self):
        for record in self:
            move_ids_name = ''
            receipt_move_ids = record.move_ids.filtered(lambda x: x.picking_type_id.code == 'incoming')
            for move in receipt_move_ids:
                move_ids_name += f', {move.reference}'
            record.move_ids_name = move_ids_name[2:] if record.move_ids else ''
            record.move_ids_date = receipt_move_ids.sorted(key=lambda r: r.date, reverse=True).mapped("date")[0] if receipt_move_ids else False

    # bill ids
    invoice_lines = fields.One2many(related="purchase_line_id.invoice_lines", string='Bills(s)')
    invoice_lines_name = fields.Text(compute='_compute_invoice_lines_name', string='Bills(s)',
        search="_search_invoice_lines_name")
    def _search_invoice_lines_name(self, operator, value):
        return [('invoice_lines.move_name', operator, value)]
    
    invoice_lines_date = fields.Datetime(compute='_compute_invoice_lines_name', string='Bill Date')

    @api.depends('purchase_id','purchase_line_id','purchase_line_id.invoice_lines','invoice_lines')
    def _compute_invoice_lines_name(self):
        for record in self:
            invoice_lines_name = ''
            for line in record.invoice_lines:
                invoice_lines_name += f', {line.move_name}'
            record.invoice_lines_name = invoice_lines_name[2:] if record.invoice_lines else ''
            record.invoice_lines_date = record.invoice_lines.sorted(key=lambda r: r.invoice_date, reverse=True).mapped("invoice_date")[0] if record.invoice_lines else False


    # purchase request line
    purchase_request_lines = fields.Many2many(related="purchase_line_id.purchase_request_lines", string='PR(s)')
    purchase_request_lines_name = fields.Text(compute='_compute_purchase_request_lines_name', string='PR(s) name',
        search="_search_purchase_request_lines_name")
    def _search_purchase_request_lines_name(self, operator, value):
        if operator == '=':
            operator = 'ilike'
        return [('purchase_line_id.purchase_request_lines.request_id.name', operator, value)]
    
    purchase_request_lines_date = fields.Datetime(compute='_compute_purchase_request_lines_name', string='PR Date')
    purchase_request_lines_qty = fields.Float(compute='_compute_purchase_request_lines_name', string='PR Quantity')
    
    @api.depends('purchase_id','purchase_line_id','purchase_line_id.purchase_request_lines','purchase_request_lines')
    def _compute_purchase_request_lines_name(self):
        for record in self:
            purchase_request_lines_name = ''
            for pr_line in record.purchase_request_lines:
                purchase_request_lines_name += f', {pr_line.request_id.name}'

            record.purchase_request_lines_name = purchase_request_lines_name[2:] if record.purchase_request_lines else ''
            record.purchase_request_lines_date = record.purchase_request_lines.sorted(key=lambda r: r.date_start, reverse=True).mapped("date_start")[0] if record.purchase_request_lines else False
            record.purchase_request_lines_qty = sum(record.purchase_request_lines.mapped("product_qty")) if record.purchase_request_lines else 0


    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE or REPLACE view """+str(self._table)+""" as (
                select 
                    row_number() over () as id, 
                    purchase_id, 
                    date_order,
                    date_planned,
                    partner_id,
                    project_id,
                    end_customer_id,
                    purchase_line_id,
                    product_id,
                    default_code,
                    pol_description,
                    product_qty
                from (
                    select 
                        pol.order_id as purchase_id, 
                        po.date_order as date_order,
                        pol.date_planned as date_planned,
                        po.partner_id as partner_id,
                        po.project_id as project_id,
                        p.partner_id as end_customer_id,

                        pol.id as purchase_line_id,
                        pol.product_id as product_id,
                        pp.default_code as default_code,
                        pol.name as pol_description,
                        pol.product_qty as product_qty

                    from purchase_order_line pol
                    left join purchase_order po on po.id = pol.order_id
                    left join project_project p on p.id = po.project_id
                    left join product_product pp on pp.id = pol.product_id
                    where po.state in ('purchase','done')
                ) as report_po_custom
            )""")
