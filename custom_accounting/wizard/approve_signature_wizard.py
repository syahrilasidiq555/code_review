from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta, date
import ast

class approve_signature_wizard(models.TransientModel):
    _name = 'approve.signature.wizard'
    _description = 'Approve Signature Wizard'

    signature = fields.Char('Signature', required=True)

    message = fields.Text('Message')

    data_id = fields.Integer(string='Data ID')
    model_name = fields.Char(string='Model Name')
    function_name = fields.Char(string='Function Name')
    # string/parameter must be "{a=1,b=2,c=3}"
    function_parameter = fields.Char(string='Function Parameter')

    # tgl JT
    invoice_date_due = fields.Date(string="Batas Waktu Berikutnya")
    
    @api.constrains('invoice_date_due')
    def _check_invoice_date_due(self):
        approved_over_due = self._context.get('default_is_approved_over_due', False)
        date_over_due = datetime.strptime(self._context.get('default_invoice_date_due', False), '%Y-%m-%d').date()
        for rec in self:
            if approved_over_due:
                if self.invoice_date_due == date_over_due:
                    raise UserError("Batas Waktu Berikutnya tidak boleh sama dengan Batas Waktu yang sebelumnya. \nBatas Waktu sebelumnya adalah {date_due}".format(date_due=str(date_over_due)))
                
                if self.invoice_date_due <= (date_over_due - timedelta(days=1)):
                    raise UserError("Batas Waktu Berikutnya tidak boleh lebih kecil dari Batas Waktu yang sebelumnya. \nBatas Waktu sebelumnya adalah {date_due}".format(date_due=str(date_over_due)))
                
                if self.invoice_date_due <= date.today():
                    raise UserError("Batas Waktu Berikutnya harus lebih dari hari ini")
    

    def btn_continue(self):
        if self.function_name:
            # self.env[self.model_name].search([('id','=',self.data_id)]).with_context(okey=True).eval(self.function_name+self.function_parameter)
            result = getattr(self.env[self.model_name].search([('id','=',self.data_id)]).with_context(\
                okey=True, message=self.message, signature=self.signature, invoice_date_due=self.invoice_date_due), self.function_name)
            if not self.function_parameter:
                return result()
            else:
                # string/parameter = "{a=1,b=2,c=3}"
                args = ast.literal_eval(self.function_parameter)
                return result(**args)
        else:
            pass