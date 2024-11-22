from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import ast
from datetime import datetime

class update_amount_wizard(models.TransientModel):
    _name = "update.amount.wizard"

    data_id = fields.Integer(string='Data ID')
    model_name = fields.Char(string='Model Name')
    function_name = fields.Char(string='Function Name')
    # string/parameter must be "{a=1,b=2,c=3}"
    function_parameter = fields.Char(string='Function Parameter')

    umk_amount = fields.Float(string='Amount', required=True)
    applied_date = fields.Date(string='Applied Date', required=True, default=datetime.now())


    def btn_continue(self):
        if self.function_name:
            # self.env[self.model_name].search([('id','=',self.data_id)]).with_context(okey=True).eval(self.function_name+self.function_parameter)
            result = getattr(self.env[self.model_name].search([('id','=',self.data_id)]).with_context(
                okey=True,
                umk_amount = self.umk_amount,
                applied_date = self.applied_date,
            ), self.function_name)
            if not self.function_parameter:
                return result()
            else:
                # string/parameter = "{a=1,b=2,c=3}"
                args = ast.literal_eval(self.function_parameter)
                return result(**args)
        else:
            pass