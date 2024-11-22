from odoo import models, fields, api, tools, _


class ReportSaleInvoice(models.Model):
    _name = "report.sale.invoice"
    _description = "Report Sale invoice"
    _auto = False
    _order = "invoice_date desc"
    _rec_name = "invoice_name"



    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    invoice_name = fields.Char(string='Invoice No.', readonly=True)
    
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    
    price_unit = fields.Monetary(string="Unit Price", readonly=True)
    price_subtotal = fields.Monetary(string="Untaxed Total", readonly=True)
    price_total = fields.Monetary(string="Total", readonly=True)

    description = fields.Char(string='Description', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    project_number = fields.Char('Project No.', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ],string='Status')


    # aggregates or computed fields
    currency_id = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id')

    @api.depends_context('allowed_company_ids')
    def _compute_currency_id(self):
        self.currency_id = self.env.company.currency_id

    def _case_value_or_one(self, value):
        return f"""CASE COALESCE({value}, 0) WHEN 0 THEN 1.0 ELSE {value} END"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE or REPLACE view {self._table}  as (
                select 
                    row_number() over () as id, 
                    am.partner_id as partner_id,
                    am.name as invoice_name,
                    am.invoice_date as invoice_date,
                    aml.quantity as quantity,
                    -- aml.price_unit as price_unit,
                    -- aml.price_subtotal as price_subtotal,
                    -- aml.price_total as price_total,

                    CASE WHEN aml.price_unit IS NOT NULL THEN (aml.price_unit
                        / {self._case_value_or_one('aml.rel_curr_rate')}
                        * {self._case_value_or_one('currency_table.rate')}
                        ) ELSE 0
                    END AS price_unit,

                    CASE WHEN aml.price_subtotal IS NOT NULL THEN (aml.price_subtotal
                        / {self._case_value_or_one('aml.rel_curr_rate')}
                        * {self._case_value_or_one('currency_table.rate')}
                        ) ELSE 0
                    END AS price_subtotal,

                    CASE WHEN aml.price_total IS NOT NULL THEN (aml.price_total
                        / {self._case_value_or_one('aml.rel_curr_rate')}
                        * {self._case_value_or_one('currency_table.rate')}
                        ) ELSE 0
                    END AS price_total,

                    aml.name as description,
                    sol.project_id as project_id,
                    pp.project_number as project_number,
                    am.company_id as company_id,
                    am.state
                
                from account_move_line aml
                left join account_move am on am.id = aml.move_id
                left join sale_order_line_invoice_rel sol_aml on sol_aml.invoice_line_id = aml.id
                left join sale_order_line sol on sol.id = sol_aml.order_line_id
                left join project_project pp on pp.id = sol.project_id
                join {self.env['res.currency']._get_query_currency_table(self.env.companies.ids, fields.Date.today())} ON currency_table.company_id = aml.company_id
                
                where am.move_type in ('out_invoice')
                and aml.display_type in ('product', 'line_section', 'line_note')
                and am.state in ('draft','posted')
                
            )""")