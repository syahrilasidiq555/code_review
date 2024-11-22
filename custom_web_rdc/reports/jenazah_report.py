from odoo import models, fields
from odoo.exceptions import UserError, ValidationError
import os
import base64

class jenazahReportMaster(models.TransientModel):
    _name = 'jenazah.report.master'
    _description = 'Jenazah Report'

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
    
    name = fields.Char(string='Name', default="Jenazah Report")
    date_begin = fields.Date(string='Begin Period',default=fields.Datetime.now)
    date_end = fields.Date(string='End Period',default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company, domain=_get_company_domain)
    report_line = fields.One2many('jenazah.report.line', 'report_id', string='Report Line', readonly=True)


    def action_search(self):
        for record in self:
            # remove line
            self.report_line = False
            report_exist = self.env[self._name].search([('id','!=',record.id)])
            if report_exist:
                report_exist.unlink()

            if (not record.date_begin and record.date_end) or (record.date_begin and not record.date_end):
                raise UserError("Anda harus pilih kedua tanggal atau tidak sama sekali!")

            where_date = "1=1 "
            if record.date_begin and record.date_end:
                where_date = "so.date_order between '{start_date} 00:00:00' and '{end_date} 23:59:59'".format(
                    start_date = record.date_begin,
                    end_date = record.date_end,
                )

            
            where_company = "1=1"
            if record.company_id:
                where_company = "company_id = {company_id}".format(
                    company_id = record.company_id.id
                )

            query = """
                select
                    so.id as so_id
                from sale_order so
                where """+where_date+"""
                AND """+where_company+"""
                --AND so.active = True                
            """
            #, sbf.product_uom_qty
            # raise UserError(query)
            # print(query)
            self.env.cr.execute(query)
            data = self.env.cr.dictfetchall()

            if data:
                report_line = map(lambda x : 
                    (0,0,{
                        'sale_order_id': x['so_id'],
                    }) , data)
                self.report_line = list(report_line)
            else:
                raise UserError("Data not found!")
        
    def action_export(self):
        for record in self:
            raise UserError("action_export!")


class jenazahReportLine(models.TransientModel):
    _name = 'jenazah.report.line'
    _description = 'Jenazah Report Line'

    report_id = fields.Many2one('jenazah.report.master', string='Report Head', ondelete="cascade")

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    partner_id = fields.Many2one(related='sale_order_id.partner_id')
    penanggungjawab_id = fields.Many2one(related='sale_order_id.penanggungjawab_id')
    state = fields.Selection(related='sale_order_id.state')

    def action_view_sale_order(self):
        for record in self:
            result = {
                'name': "Sale Order",
                'type': 'ir.actions.act_window',
                # 'view_id': self.env.ref('purchase.purchase_order_form').id, 
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': record.id,
                # 'domain': [('id', 'in', self.move_ids.ids)],
                'context': {'create': False, 'edit': False},
            }
            return result

    # def action_view_move_ids(self):
    #     result = {
    #         'name': "Stock Move",
    #         'type': 'ir.actions.act_window',
    #         # 'view_id': self.env.ref('purchase.purchase_order_form').id, 
    #         'res_model': 'stock.move',
    #         'view_mode': 'tree,form',
    #         'domain': [('id', 'in', self.move_ids.ids)],
    #         'context': {'create': False},
    #     }
    #     return result