from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.constrains('groups_id')
    def _constrains_groups_add(self):
        for record in self:
            not_allowed_groups = eval(self.env['ir.config_parameter'].sudo().get_param('custom_access_right.not_allowed_groups_ids')) if self.env['ir.config_parameter'].sudo().get_param('custom_access_right.not_allowed_groups_ids') else []
            
            if not_allowed_groups and self.env.user.id == record.id:
                if not self.env.user.has_group("base.group_system") and len(list(set(record.groups_id.ids).intersection(not_allowed_groups))) >= 1:
                    message = "Hanya user dengan access group Administrasi / Pengaturan yang dapat menambahkan anda ke group yang ada di list sebagai berikut : \n\n"
                    
                    grouplist = self.env['res.groups'].search([('id','in',not_allowed_groups)])
                    for group in grouplist:
                        message += "- %s \n" % group.display_name

                    raise ValidationError(message)
        
    
    product_category_ids = fields.Many2many('product.category', string='Hide Product Based on Category')
