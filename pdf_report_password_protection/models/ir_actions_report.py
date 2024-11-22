# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, api
from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader


class IrActionsReportInherit(models.Model):
    """The Class Inherits to update the fields and functions"""
    _inherit = 'ir.actions.report'

    is_password = fields.Boolean("Enable Password?",
                                help="Activate this field if you want to add "
                                    "the password for pdf report")
    
    password_type = fields.Selection([
        ('static', 'Static'),
        ('dynamic', 'Dynamic'),
    ], string='Password Type', default="static", required=True)
    password_field_id = fields.Many2one('ir.model.fields', string='Password Field')
    password_name = fields.Char("Password", help="Enter the Password here")
    # Encrypts the given PDF data with a specified password if
    # the password protection is enabled.
    def apply_password_protection(self, pdf_content, pwd=False):
        """Method Added to Implement the pasword options"""
        input_buffer = BytesIO(pdf_content)
        reader = PdfFileReader(input_buffer)
        writer = PdfFileWriter()
        writer.appendPagesFromReader(reader)
        if self.is_password:
            # print(self.env.context)
            # print("ini context")
            if self.password_type == 'dynamic':
                model_pwd = self.env[self.model].browse(self.env.context.get('active_id'))
                user_pwd = eval(f'model_pwd.{self.password_field_id.name}') if model_pwd else ' '
                writer.encrypt(user_pwd=user_pwd, owner_pwd=None,
                            use_128bit=True)
            else:
                writer.encrypt(user_pwd=self.password_name, owner_pwd=None,
                            use_128bit=True)
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.read()

    # def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
    #     res = super()._render_qweb_pdf(report_ref=report_ref, res_ids=res_ids, data=data)
    #     if res and res[0]:
    #         content = self.apply_password_protection(res[0], self.password_name)
    #         print("masuk sini duluheheheheheh")
    #         print(f'ref:{report_ref}\npass : {self.is_password}\ncontext:{self.env.context}\npass:{self.password_name}\n')
    #         return content, 'pdf'
        
    #         # report_obj = self.env.ref(report_ref)
    #         # if report_obj:
    #         #     content = report_obj.apply_password_protection(res[0], report_obj.password_name)
    #         # print("masuk sini duluheheheheheh")
    #         # print(f'pass : {report_obj.is_password}\ncontext:{self.env.context}\npass:{report_obj.password_name}')
    #         # return content, 'pdf'
    #     return res

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        res = super()._render_qweb_pdf(report_ref=report_ref, res_ids=res_ids, data=data)
        # print(f"ini ids : {res_ids}")
        if res and res[0]:
            report_obj = self._get_report(report_ref)
            if report_obj:
            
                content = report_obj.with_context({'active_id':res_ids}).apply_password_protection(res[0], report_obj.password_name)
                # print("masuk sini duluheheheheheh")
                # print(f'pass : {report_obj.is_password}\ncontext:{self.env.context}\npass:{report_obj.password_name}')
                return content, 'pdf'
        return res