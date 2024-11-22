# from attr import field
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from odoo.tools import float_round, float_repr

from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

import re

FK_HEAD_LIST = ['FK', 'KD_JENIS_TRANSAKSI', 'FG_PENGGANTI', 'NOMOR_FAKTUR', 'MASA_PAJAK', 'TAHUN_PAJAK', 'TANGGAL_FAKTUR', 'NPWP', 'NAMA', 'ALAMAT_LENGKAP', 'JUMLAH_DPP', 'JUMLAH_PPN', 'JUMLAH_PPNBM', 'ID_KETERANGAN_TAMBAHAN', 'FG_UANG_MUKA', 'UANG_MUKA_DPP', 'UANG_MUKA_PPN', 'UANG_MUKA_PPNBM', 'REFERENSI', 'KODE_DOKUMEN_PENDUKUNG']

LT_HEAD_LIST = ['LT', 'NPWP', 'NAMA', 'JALAN', 'BLOK', 'NOMOR', 'RT', 'RW', 'KECAMATAN', 'KELURAHAN', 'KABUPATEN', 'PROPINSI', 'KODE_POS', 'NOMOR_TELEPON']

OF_HEAD_LIST = ['OF', 'KODE_OBJEK', 'NAMA', 'HARGA_SATUAN', 'JUMLAH_BARANG', 'HARGA_TOTAL', 'DISKON', 'DPP', 'PPN', 'TARIF_PPNBM', 'PPNBM']


def _csv_row(data, delimiter=',', quote='"'):
    return quote + (quote + delimiter + quote).join([str(x).replace(quote, '\\' + quote) for x in data]) + quote + '\n'
class account_move(models.Model):
    _inherit = "account.move"

    # FOR TAXES
    tax_date = fields.Date(string="Tax Date", store=True)
    efaktur_id = fields.Many2one('l10n_id_efaktur.efaktur.range')

    # ADD PO, SO, COST SHEET FIELD if exist
    po_id = fields.Many2one('purchase.order', string='Purchase Order', compute="_compute_invoice_origin", store=True)
    so_id = fields.Many2one('sale.order', string='Sale Order', compute="_compute_invoice_origin", store=True)

    @api.depends('invoice_origin')
    def _compute_invoice_origin(self):
        for record in self:
            record.po_id = None
            record.so_id = None
            
            if record.invoice_origin:
                # cari PO & SO
                purchase_order = self.env['purchase.order'].sudo().search([('name','=',record.invoice_origin)], limit=1)
                sale_order = self.env['sale.order'].sudo().search([('name','=',record.invoice_origin)], limit=1)

                if purchase_order:
                    record.po_id = purchase_order[0].id
                    
                elif sale_order:
                    record.so_id = sale_order[0].id

    # for password invoice
    customer_id_pass = fields.Char(compute='_compute_customer_id_pass', string='Customer ID Pass')
    
    @api.depends('partner_id','partner_id.customer_id')
    def _compute_customer_id_pass(self):
        for record in self:
            customer_id_pass = ' '
            if record.partner_id and record.partner_id.customer_id:
                customer_id_pass = record.partner_id.customer_id[-4:] if record.partner_id.customer_id[-4:] else customer_id_pass
            record.customer_id_pass = customer_id_pass

    last_month_move_ids = fields.Many2many('account.move', compute='_compute_last_month_move_ids', string='Move Last Month')

    @api.depends('write_date','invoice_date','state','move_type', 'partner_id')
    def _compute_last_month_move_ids(self):
        for record in self:
            last_month_move_ids = False
            if record.move_type == 'out_invoice' and record.invoice_date and record.partner_id:
                last_month = record.invoice_date - relativedelta(months=1)

                start_date = last_month.replace(day=1)
                next_month = last_month.replace(day=28) + relativedelta(days=4)
                end_date = next_month.replace(day=1) - relativedelta(days=1)

                # print(last_month)
                # print('==============')
                # print(start_date)
                # print(end_date)

                move_ids = self.env[self._name].search([
                    ('partner_id','=',record.partner_id.id),
                    ('invoice_date','>=',start_date),
                    ('invoice_date','<=',end_date),
                    ('move_type','=',record.move_type),
                    ('state','=',['posted']),
                ])
                if move_ids:
                    last_month_move_ids = [(4,move.id) for move in move_ids]
            record.last_month_move_ids = last_month_move_ids

    amount_residual_cumulative = fields.Monetary(compute='_compute_amount_residual_cumulative', string='Amount Due Cumulative')
    
    @api.depends('last_month_move_ids','amount_residual')
    def _compute_amount_residual_cumulative(self):
        for record in self:
            amount_residual_cumulative = record.amount_residual

            for inv in record.last_month_move_ids:
                amount_residual_cumulative += inv.amount_residual

            record.amount_residual_cumulative = amount_residual_cumulative

    def action_register_payment(self):
        last_month_line_ids = []
        for inv in self.last_month_move_ids:
            last_month_line_ids += [line.id for line in inv.line_ids] 
        line_ids = self.env['account.move.line'].browse([line.id for line in self.line_ids] + last_month_line_ids)
        # raise UserError(line_ids)
        return line_ids.action_register_payment()
    
    # edit printout invoice name
    def _get_move_display_name(self, show_ref=False):
        res = super()._get_move_display_name(show_ref=show_ref)
        self.ensure_one()
        if self.state != 'draft' and self.so_id and self.so_id.invoice_id:
            name = f'{self.so_id.invoice_id} {self.name}'
            return name + f' {self.invoice_date.year}-{self.invoice_date.month}' if self.invoice_date else name
        return res + f' {self.invoice_date.year}-{self.invoice_date.month}' if self.invoice_date else res
    
    @api.constrains('l10n_id_tax_number')
    def _constrains_l10n_id_tax_number(self):
        for record in self.filtered('l10n_id_tax_number'):
            # if record.l10n_id_tax_number != re.sub(r'\D', '', record.l10n_id_tax_number):
            #     record.l10n_id_tax_number = re.sub(r'\D', '', record.l10n_id_tax_number)
            if len(record.l10n_id_tax_number) != 16:
                # raise UserError(_('A tax number should have 16 digits'))
                pass
            elif record.l10n_id_tax_number[:2] not in dict(self._fields['l10n_id_kode_transaksi'].selection).keys():
                raise UserError(_('A tax number must begin by a valid Kode Transaksi'))
            elif record.l10n_id_tax_number[2] not in ('0', '1'):
                raise UserError(_('The third digit of a tax number must be 0 or 1'))

    def _post(self, soft=True):
        for move in self:
            if move.l10n_id_need_kode_transaksi:
                if not move.l10n_id_kode_transaksi:
                    raise ValidationError(_('You need to put a Kode Transaksi for this partner.'))
                if move.l10n_id_replace_invoice_id.l10n_id_tax_number:
                    if not move.l10n_id_replace_invoice_id.l10n_id_attachment_id:
                        raise ValidationError(_('Replacement invoice only for invoices on which the e-Faktur is generated. '))
                    rep_efaktur_str = move.l10n_id_replace_invoice_id.l10n_id_tax_number
                    move.l10n_id_tax_number = '%s1%s' % (move.l10n_id_kode_transaksi, rep_efaktur_str[3:])
                else:
                    efaktur, dt_efaktur = self.env['l10n_id_efaktur.efaktur.range'].pop_number_2(move.company_id.id)
                    if not efaktur:
                        raise ValidationError(_('There is no Efaktur number available.  Please configure the range you get from the government in the e-Faktur menu. '))
                    if dt_efaktur:
                        move.sudo().write({'efaktur_id':dt_efaktur.id})
                    move.l10n_id_tax_number = '%s0%013d' % (str(move.l10n_id_kode_transaksi), efaktur)

        res = super()._post(soft)
        for move in self:
            if not move.tax_date:
                move.tax_date = move.invoice_date
            if move.l10n_id_tax_number:
                move.l10n_id_tax_number = str(move.l10n_id_tax_number)[:3] + str(move.efaktur_id.prefix) + str(move.l10n_id_tax_number)[4:13]
        return res
    
    def _generate_efaktur_invoice(self, delimiter):
        """Generate E-Faktur for customer invoice."""
        # Invoice of Customer

        output_head = '%s%s%s' % (
            _csv_row(FK_HEAD_LIST, delimiter),
            _csv_row(LT_HEAD_LIST, delimiter),
            _csv_row(OF_HEAD_LIST, delimiter),
        )

        idr = self.env.ref('base.IDR')

        for move in self.filtered(lambda m: m.state == 'posted'):
            eTax = move._prepare_etax()

            commercial_partner = move.partner_id.commercial_partner_id
            nik = str(commercial_partner.l10n_id_nik) if not commercial_partner.vat else ''

            if move.l10n_id_replace_invoice_id:
                number_ref = str(move.l10n_id_replace_invoice_id.name) + " replaced by " + str(move.name) + " " + nik
            else:
                number_ref = str(move.name) + " " + nik

            street = ', '.join([x for x in (move.partner_id.street, move.partner_id.street2) if x])

            invoice_npwp = '000000000000000'
            if commercial_partner.vat and len(commercial_partner.vat) >= 12:
                invoice_npwp = commercial_partner.vat
            elif (not commercial_partner.vat or len(commercial_partner.vat) < 12) and commercial_partner.l10n_id_nik:
                invoice_npwp = commercial_partner.l10n_id_nik
            invoice_npwp = invoice_npwp.replace('.', '').replace('-', '')

            # Here all fields or columns based on eTax Invoice Third Party
            eTax['KD_JENIS_TRANSAKSI'] = move.l10n_id_tax_number[0:2] or 0
            eTax['FG_PENGGANTI'] = move.l10n_id_tax_number[2:3] or 0
            eTax['NOMOR_FAKTUR'] = move.l10n_id_tax_number[:] or 0 # here
            eTax['MASA_PAJAK'] = move.invoice_date.month
            eTax['TAHUN_PAJAK'] = move.invoice_date.year
            eTax['TANGGAL_FAKTUR'] = '{0}/{1}/{2}'.format(move.invoice_date.day, move.invoice_date.month, move.invoice_date.year)
            eTax['NPWP'] = invoice_npwp
            eTax['NAMA'] = move.partner_id.name if eTax['NPWP'] == '000000000000000' else commercial_partner.l10n_id_tax_name or move.partner_id.name
            eTax['ALAMAT_LENGKAP'] = move.partner_id.contact_address.replace('\n', '') if eTax['NPWP'] == '000000000000000' else commercial_partner.l10n_id_tax_address or street
            eTax['JUMLAH_DPP'] = int(float_round(move.amount_untaxed, 0, rounding_method="DOWN"))  # currency rounded to the unit
            eTax['JUMLAH_PPN'] = int(float_round(move.amount_tax, 0, rounding_method="DOWN"))  # tax amount ALWAYS rounded down
            eTax['ID_KETERANGAN_TAMBAHAN'] = '1' if move.l10n_id_kode_transaksi == '07' else ''
            eTax['REFERENSI'] = number_ref
            eTax['KODE_DOKUMEN_PENDUKUNG'] = '0'

            lines = move.line_ids.filtered(lambda x: x.move_id._is_downpayment() and x.price_unit < 0 and x.display_type == 'product')
            eTax['FG_UANG_MUKA'] = 0
            eTax['UANG_MUKA_DPP'] = float_repr(abs(sum(lines.mapped(lambda l: float_round(l.price_subtotal, 0)))), 0)
            eTax['UANG_MUKA_PPN'] = float_repr(abs(sum(lines.mapped(lambda l: float_round(l.price_total - l.price_subtotal, 0)))), 0)

            fk_values_list = ['FK'] + [eTax[f] for f in FK_HEAD_LIST[1:]]

            # HOW TO ADD 2 line to 1 line for free product
            free, sales = [], []

            for line in move.line_ids.filtered(lambda l: l.display_type == 'product'):
                # *invoice_line_unit_price is price unit use for harga_satuan's column
                # *invoice_line_quantity is quantity use for jumlah_barang's column
                # *invoice_line_total_price is bruto price use for harga_total's column
                # *invoice_line_discount_m2m is discount price use for diskon's column
                # *line.price_subtotal is subtotal price use for dpp's column
                # *tax_line or free_tax_line is tax price use for ppn's column
                free_tax_line = tax_line = 0.0

                for tax in line.tax_ids:
                    if tax.amount > 0:
                        tax_line += line.price_subtotal * (tax.amount / 100.0)

                discount = 1 - (line.discount / 100)
                # guarantees price to be tax-excluded
                invoice_line_total_price = line.price_subtotal / discount if discount else 0
                invoice_line_unit_price = invoice_line_total_price / line.quantity if line.quantity else 0

                line_dict = {
                    'KODE_OBJEK': line.product_id.default_code or '',
                    'NAMA': line.product_id.name or '',
                    'HARGA_SATUAN': float_repr(idr.round(invoice_line_unit_price), idr.decimal_places),
                    'JUMLAH_BARANG': line.quantity,
                    'HARGA_TOTAL': idr.round(invoice_line_total_price),
                    'DPP': line.price_subtotal,
                    'product_id': line.product_id.id,
                }

                if line.price_subtotal < 0:
                    for tax in line.tax_ids:
                        free_tax_line += (line.price_subtotal * (tax.amount / 100.0)) * -1.0

                    line_dict.update({
                        'DISKON': float_round(invoice_line_total_price - line.price_subtotal, 0),
                        'PPN': free_tax_line,
                    })
                    free.append(line_dict)
                elif line.price_subtotal != 0.0:
                    invoice_line_discount_m2m = invoice_line_total_price - line.price_subtotal

                    line_dict.update({
                        'DISKON': float_round(invoice_line_discount_m2m, 0),
                        'PPN': tax_line,
                    })
                    sales.append(line_dict)

            sub_total_before_adjustment = sub_total_ppn_before_adjustment = 0.0

            # We are finding the product that has affected
            # by free product to adjustment the calculation
            # of discount and subtotal.
            # - the price total of free product will be
            # included as a discount to related of product.
            for sale in sales:
                for f in free:
                    if f['product_id'] == sale['product_id']:
                        sale['DISKON'] = sale['DISKON'] - f['DISKON'] + f['PPN']
                        sale['DPP'] = sale['DPP'] + f['DPP']

                        tax_line = 0

                        for tax in line.tax_ids:
                            if tax.amount > 0:
                                tax_line += sale['DPP'] * (tax.amount / 100.0)

                        sale['PPN'] = tax_line

                        free.remove(f)

                sub_total_before_adjustment += sale['DPP']
                sub_total_ppn_before_adjustment += sale['PPN']

                sale.update({
                    # Use the db currency rounding to float_round the DPP/PPN.
                    # As we will correct them we need them to be close to the final result.
                    'DPP': idr.round(sale['DPP']),
                    'PPN': idr.round(sale['PPN']),
                    'DISKON': float_repr(sale['DISKON'], 0),
                })


            # The total of the base (DPP) and taxes (PPN) must be a integer, equal to the JUMLAH_DPP and JUMLAH_PPN
            # To do so, we adjust the first line in order to achieve the correct total
            if sales:
                diff_dpp = idr.round(eTax['JUMLAH_DPP'] - sum([sale['DPP'] for sale in sales]))
                total_sales_ppn = idr.round(eTax['JUMLAH_PPN'] - sum([sale['PPN'] for sale in sales]))
                # We will add the differences to the first line for which adding the difference will not result in a negative value.
                for sale in sales:
                    if sale['DPP'] + diff_dpp >= 0 and sale['PPN'] + total_sales_ppn >= 0:
                        sale['HARGA_TOTAL'] += diff_dpp
                        sale['DPP'] += diff_dpp
                        diff_dpp = 0
                        sale['PPN'] += total_sales_ppn
                        total_sales_ppn = 0
                        break

                # We couldn't adjust everything in a single line as their values is too low.
                # So we will instead slit the adjustment in multiple lines.
                if diff_dpp or total_sales_ppn:
                    for sale in sales:
                        # DPP
                        sale_dpp = sale['DPP']
                        sale["DPP"] = max(0, sale["DPP"] + diff_dpp)
                        diff_dpp -= (sale["DPP"] - sale_dpp)
                        sale['HARGA_TOTAL'] = sale["DPP"]
                        # PPN
                        sale_ppn = sale['PPN']
                        sale["PPN"] = max(0, sale["PPN"] + total_sales_ppn)
                        total_sales_ppn -= (sale["PPN"] - sale_ppn)

            # Values now being corrected, we can format them for the CSV
            for sale in sales:
                sale.update({
                    'HARGA_TOTAL': float_repr(sale['HARGA_TOTAL'], idr.decimal_places),
                    'DPP': float_repr(sale['DPP'], idr.decimal_places),
                    'PPN': float_repr(sale['PPN'], idr.decimal_places),
                })

            output_head += _csv_row(fk_values_list, delimiter)
            for sale in sales:
                of_values_list = ['OF'] + [str(sale[f]) for f in OF_HEAD_LIST[1:-2]] + ['0', '0']
                output_head += _csv_row(of_values_list, delimiter)

        return output_head

    # def get_invoice_pdf_report_attachment(self):
    #     if len(self) < 2 and self.invoice_pdf_report_id:
    #         # if the Send & Print succeeded
    #         return self.invoice_pdf_report_id.raw, self.invoice_pdf_report_id.name
    #     elif len(self) < 2 and self.message_main_attachment_id:
    #         # if the Send & Print failed with fallback=True -> proforma PDF
    #         return self.message_main_attachment_id.raw, self.message_main_attachment_id.name
    #     # all other cases
    #     pdf_content = self.env['ir.actions.report']._render('account.account_invoices', self.ids)[0]
    #     pdf_content_pass = self.env['ir.actions.report']._get_report_from_name('account.account_invoices').apply_password_protection(pdf_content)
    #     pdf_name = self._get_move_display_name() if len(self) == 1 else "Invoices.pdf"
    #     return pdf_content_pass, pdf_name