# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime
import json

class ProductCategory(models.Model):
    _inherit = "product.category"

    def get_xml_id(self):
        for record in self:
            domain = [('model', '=', record._name), ('res_id', '=', record.id)]
            model_data = self.env['ir.model.data'].search(domain, limit=1)
            xml_id = "%s.%s" % (model_data.module, model_data.name)
            return xml_id

    def unlink(self):
        for record in self:
            xml_id = record.get_xml_id()
            # raise UserError(str(True if))
            if xml_id and 'False' not in str(xml_id):
                raise ValidationError("Anda tidak dapat menghapus record yang dibuat oleh sistem, anda hanya dapat melakukan rename pada record ini\n\nKategori: %s" % record.name)
        return super(ProductCategory, self).unlink()