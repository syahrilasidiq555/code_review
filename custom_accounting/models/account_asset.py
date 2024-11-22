from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    code_name = fields.Char(string='Asset Number', store=True, readonly=True, default=lambda self: ('New'))
    abbreviation = fields.Char(string='Abbreviation', size=5, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, domain="[('company_id', '=', company_id), ('is_off_balance', '=', False)]")

    @api.constrains('model_id')
    def _constrains_model_id(self):
        for rec in self:
            if not rec.model_id.abbreviation and rec.state not in ['model','open']:
                raise ValidationError("You must set the Abbreviation in Asset Category!")
    

    def validate(self):
        res = super(AccountAsset, self).validate()
        for record in self.filtered(lambda x: x.code_name == 'New'):
            code_name =  self.env['ir.sequence'].get_sequence(self._name, f'FA/{record.model_id.abbreviation}/{record.acquisition_date.strftime("%m%y")}', padding=3)
            record.write({'code_name': code_name})