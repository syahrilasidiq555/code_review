# -*- coding: utf-8 -*-
from markupsafe import Markup
from werkzeug.urls import url_encode

from odoo import _, api, fields, models, modules, tools, Command
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

import base64

class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    def _compute_mail_attachments_widget(self):
        res = super(AccountMoveSend, self)._compute_mail_attachments_widget()
        for record in self:
            record.mail_attachments_widget = []
            record.mail_attachments_widget = record._get_pdf_invoice(record.move_ids, 'account.account_invoices')
            

    def _get_pdf_invoice(self, move_ids, report_name):
        report = self.env.ref(report_name)
        pdf = report._render_qweb_pdf(report_name, move_ids.ids)

        b64_pdf = base64.b64encode(pdf[0])
        # save pdf as attachment
        name = move_ids._get_move_display_name() if len(move_ids) == 1 else 'Invoices'
        attachment = self.env['ir.attachment'].sudo().create({
            'name': name,
            'type': 'binary',
            'res_id': self.id,
            'res_model': self._name,
            'datas': b64_pdf,
            # 'public': True if active_model == 'hr.leave' else False,
        })
        if attachment:
            return [{
                'id': attachment.id,
                'name': attachment.name,
                'mimetype': attachment.mimetype,
                'placeholder': False,
                'protect_from_deletion': True,
            }]
        return []



    # @api.model
    def _process_send_and_print(self, moves, wizard=None, allow_fallback_pdf=False, **kwargs):
        """ Process the moves given their individual configuration set on move.send_and_print_values.
        :param moves: account.move to process
        :param wizard: account.move.send wizard if exists. If not we avoid raising any error.
        :param allow_fallback_pdf:  In case of error when generating the documents for invoices, generate a proforma PDF report instead.
        """
        from_cron = not wizard

        moves_data = {
            move: {
                **(move.send_and_print_values if not wizard else wizard._get_wizard_values()),
                **self._get_mail_move_values(move, wizard),
            }
            for move in moves
        }

        # Generate all invoice documents.
        # self._generate_invoice_documents(moves_data, allow_fallback_pdf=allow_fallback_pdf)

        # Manage errors.
        errors = {move: move_data for move, move_data in moves_data.items() if move_data.get('error')}
        if errors:
            self._hook_if_errors(errors, from_cron=from_cron, allow_fallback_pdf=allow_fallback_pdf)

        # Fallback in case of error.
        errors = {move: move_data for move, move_data in moves_data.items() if move_data.get('error')}
        if allow_fallback_pdf and errors:
            self._generate_invoice_fallback_documents(errors)

        # Send mail.
        success = {move: move_data for move, move_data in moves_data.items() if not move_data.get('error')}
        if success:
            self._hook_if_success(success, from_cron=from_cron, allow_fallback_pdf=allow_fallback_pdf)

        # Update send and print values of moves
        for move, move_data in moves_data.items():
            if from_cron and move_data.get('error'):
                move.send_and_print_values = {'error': True}
            else:
                move.send_and_print_values = False

        # to_download = {move: move_data for move, move_data in moves_data.items() if move_data.get('download')}
        # if to_download:
        #     attachment_ids = []
        #     for move, move_data in to_download.items():
        #         attachment_ids += self._get_invoice_extra_attachments(move).ids or move_data.get('proforma_pdf_attachment').ids
        #     if attachment_ids:
        #         if kwargs.get('bypass_download'):
        #             return attachment_ids
        #         return self._download(attachment_ids, to_download)

        return {'type': 'ir.actions.act_window_close'}

    # def _prepare_invoice_pdf_report(self, invoice, invoice_data):
    #     """ Prepare the pdf report for the invoice passed as parameter.
    #     :param invoice:         An account.move record.
    #     :param invoice_data:    The collected data for the invoice so far.
    #     """
    #     if invoice.invoice_pdf_report_id:
    #         return

    #     content, _report_format = self.env['ir.actions.report']._render('account.account_invoices', invoice.ids)
    #     content_pass = self.env['ir.actions.report']._get_report_from_name('account.account_invoices').apply_password_protection(content)

    #     invoice_data['pdf_attachment_values'] = {
    #         'raw': content_pass,
    #         # 'name': invoice._get_invoice_report_filename(),
    #         'name': "asdasdas",
    #         'mimetype': 'application/pdf',
    #         'res_model': invoice._name,
    #         'res_id': invoice.id,
    #         'res_field': 'invoice_pdf_report_file', # Binary field
    #     }



    # def _prepare_invoice_proforma_pdf_report(self, invoice, invoice_data):
    #     """ Prepare the proforma pdf report for the invoice passed as parameter.
    #     :param invoice:         An account.move record.
    #     :param invoice_data:    The collected data for the invoice so far.
    #     """
    #     content, _report_format = self.env['ir.actions.report']._render('account.account_invoices', invoice.ids, data={'proforma': True})
    #     content_pass = self.env['ir.actions.report']._get_report_from_name('account.account_invoices').apply_password_protection(content)

    #     invoice_data['proforma_pdf_attachment_values'] = {
    #         'raw': content_pass,
    #         # 'name': invoice._get_invoice_proforma_pdf_report_filename(),
    #         'name': "asdasdas",
    #         'mimetype': 'application/pdf',
    #         'res_model': invoice._name,
    #         'res_id': invoice.id,
    #     }

