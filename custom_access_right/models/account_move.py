# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from datetime import date, datetime

class AccountMove(models.Model):
    _inherit = "account.move"


    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 
    # BUTTON CONFIRM
    def action_post(self):
        res = super(AccountMove, self).action_post()
        group_confirm_discount = 'custom_access_right.group_am_button_action_post_discount'
        group_obj = self.env.ref(group_confirm_discount)
        for record in self:
            if record.is_discount and not self.env.user.has_group(group_confirm_discount):
                msg = "Anda tidak dapat konfirmasi record dengan diskon yang diisi, silahkan lakukan konfimasi dengan user yang memiliki akses group berikut :\n\n"
                msg += "- %s" % group_obj.name
                raise ValidationError(msg)
            
        return res