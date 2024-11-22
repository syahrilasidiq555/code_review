from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date

import ast

class confirm_wizard(models.TransientModel):
    _name = 'confirm.wizard'
    _description = 'Confirm Wizard'

    message = fields.Text('Message')

    data_id = fields.Integer(string='Data ID')
    model_name = fields.Char(string='Model Name')
    function_name = fields.Char(string='Function Name')
    # string/parameter must be "{a=1,b=2,c=3}"
    function_parameter = fields.Char(string='Function Parameter')


    recipent_user_id = fields.Many2one('res.users', string='Recipent User')


    def btn_continue(self):
        send_email = self.env.context.get('send_reminder')
        if send_email and not self.recipent_user_id:
            raise UserError("Anda harus mengisi user terlebih dahulu!")

        if self.function_name:
            # self.env[self.model_name].search([('id','=',self.data_id)]).with_context(okey=True).eval(self.function_name+self.function_parameter)
            result = getattr(self.env[self.model_name].search([('id','=',self.data_id)]).with_context(okey=True, message=self.message, recipent_user_id=self.recipent_user_id.id), self.function_name)
            if not self.function_parameter:
                return result()
            else:
                # string/parameter = "{a=1,b=2,c=3}"
                args = ast.literal_eval(self.function_parameter)
                return result(**args)
        else:
            pass