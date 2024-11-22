import base64
from calendar import month
from codecs import namereplace_errors
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

import calendar
from datetime import datetime

import os
import math

import numpy as np

class WizardExportPayslip(models.Model):
    _name = 'wizard.export.payslip'
    _description = "Export Payslip"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    periode = fields.Date(string="Periode", default=fields.Datetime.now, required=True, format="%m%y")

    def _default_month(self):
        ayeuna = datetime.today()
        return str(ayeuna.month)
    month = fields.Selection(
        string='Month',
        selection=[
            ('1', 'Januari'), 
            ('2', 'Februari'),
            ('3', 'Maret'),
            ('4', 'April'),
            ('5', 'Mei'),
            ('6', 'Juni'),
            ('7', 'Juli'),
            ('8', 'Agustus'),
            ('9', 'September'),
            ('10', 'Oktober'),
            ('11', 'November'),
            ('12', 'Desember'),
        ], default=_default_month)

    def _default_year(self):
        ayeuna = datetime.today()
        return ayeuna.year
    year = fields.Char(string='Year', default=_default_year)
    
    date_begin = fields.Date(string="Begin", default=fields.Datetime.now, required=True)
    date_end = fields.Date(string="End", default=fields.Datetime.now, required=True)

    def action_export(self):
        datestring = "{}-{}-1".format(self.year, self.month)
        self.date_begin = datetime.strptime(datestring, '%Y-%m-%d')
        self.date_end = self.date_begin + relativedelta(day=calendar.monthrange(self.date_begin.year, self.date_begin.month)[1])

        import xlwt
        from xlwt import Workbook

        # Header
        header_font = xlwt.Font()
        header_font.bold = True

        header_align = xlwt.Alignment()
        header_align.horz = xlwt.Alignment.HORZ_CENTER
        header_align.wrap = xlwt.Alignment.WRAP_AT_RIGHT

        header_style = xlwt.XFStyle()
        header_style.font = header_font
        header_style.alignment = header_align

        # Header Title
        header_title_font = xlwt.Font()
        header_title_font.bold = True

        header_title = xlwt.XFStyle()
        header_title.font = header_title_font

        # DATE STYLE
        date_style = xlwt.XFStyle()
        date_style.num_format_str = 'DD-MMM-YYYY'

        # FLOAT STYLE
        float_style = xlwt.XFStyle()
        float_style.num_format_str = '_-* #,##0.00_-;-* #,##0.00_-;_-* "-"??_-;_-@_-'

        float_rp_style = xlwt.XFStyle()
        float_rp_style.num_format_str = '_-Rp* #,##0.00_-;-* #,##0.00_-;_-* "-"??_-;_-@_-'

        # PERCENTAGE STYLE
        percen_style = xlwt.XFStyle()
        percen_style.num_format_str = '0%'

        # INTEGER STYLE
        int_style = xlwt.XFStyle()
        int_style.num_format_str = '#,##0'

        wb = Workbook()

        # SHEET REPORT PAYSLIP ---------------------------------------------------------
        sheet1 = wb.add_sheet('Report Payslip')
        #sheet1.write(row,col, data, style)
        #_-* #.##0,00_-;-* #.##0,00_-;_-* "-"??_-;_-@_-        

        sheet1.col(0).width = 1000 #no
        sheet1.col(1).width = 4500 #nik
        sheet1.col(2).width = 4500 #no ktp
        sheet1.col(3).width = 8500 #nama
        sheet1.col(4).width = 4500 #no ktp
        sheet1.col(5).width = 4500 #no ktp
        sheet1.col(6).width = 4500 #no ktp

        judul = "Report Payslip " + self.company_id.name + " Periode " + str(self.date_begin.strftime('%B %Y'))
        periode = self.date_begin
        start_date = datetime(periode.year, periode.month, 1)
        res = calendar.monthrange(periode.year, periode.month)
        day = res[1]
        end_date = datetime(periode.year, periode.month, day)

        row = 0
        sheet1.write(row, 0, self.company_id.name, header_title) 
        row += 1
        sheet1.write(row, 0, judul, header_title) 

        row += 2
        sheet1.write(row, 0, "No", header_style)
        sheet1.write(row, 1, "NIK", header_style)
        sheet1.write(row, 2, "No. KTP", header_style)
        sheet1.write(row, 3, "Nama", header_style)
        sheet1.write(row, 4, "Department", header_style)
        sheet1.write(row, 5, "Section", header_style)
        sheet1.write(row, 6, "Jabatan", header_style)
        lastCol = 6
        dtPay = self.env['hr.payslip'].search([
            ('date_to','>=',self.date_begin),
            ('date_to','<=',self.date_end),
            ('state','=','done')])
        mapped_rule = dtPay.line_ids.mapped('salary_rule_id')
        list_nothing = []
        for rule in mapped_rule:
            sumCol = sum(dtPay.line_ids.filtered(lambda r: r.salary_rule_id.id == rule.id).mapped("total"))
            if sumCol != 0:
                sheet1.col(lastCol+1).width = 3800 
                sheet1.write(row, lastCol+1, rule.code, header_style)
                lastCol += 1
            else:
                list_nothing.append(rule.code)

        row += 1
        idx = 0
        for pay in dtPay:
            sheet1.write(row, 0, idx + 1, int_style)
            sheet1.write(row, 1, pay.employee_id.barcode if pay.employee_id.barcode else "")
            sheet1.write(row, 2, pay.employee_id.identification_id if pay.employee_id.identification_id else "")
            sheet1.write(row, 3, pay.employee_id.name)
            sheet1.write(row, 4, pay.employee_id.department_id.name if pay.employee_id.department_id else "")
            sheet1.write(row, 5, pay.employee_id.section.name if pay.employee_id.section else "")
            sheet1.write(row, 6, pay.employee_id.job_id.name if pay.employee_id.job_id else "")
            lastCol = 6
            for line in pay.line_ids:
                lastCol = 6
                for map in mapped_rule.filtered(lambda r: r.code not in list_nothing):
                    if map.id == line.salary_rule_id.id:
                        sheet1.write(row, lastCol+1, line.total, float_style)
                        lastCol += 1
                        break
                    lastCol += 1
            row += 1
            idx += 1

        # SHEET RUT ---------------------------------------------------------
        sheet2 = wb.add_sheet('RUT')
        sheet2.col(0).width = 1000 #no
        sheet2.col(1).width = 4500 #nm dept
        sheet2.col(2).width = 8000 #nm pgw
        sheet2.col(3).width = 2000 #group pjk
        sheet2.col(4).width = 3500 #rek
        sheet2.col(5).width = 3500 # Nik
        sheet2.col(6).width = 3500 # payroll code
        sheet2.col(7).width = 4500 # section
        sheet2.col(8).width = 3500 # unit
        sheet2.col(9).width = 5500 # jabatan / job id
        sheet2.col(10).width = 3800 # net salary

        judul = str(self.date_begin.strftime('%Y%m'))
        row = 0
        sheet2.write(row, 0, self.company_id.name, header_title) 
        row += 1
        sheet2.write(row, 0, judul, header_title) 
        row += 2

        sheet2.write(row, 0, "No", header_style)
        sheet2.write(row, 1, "DEPARTMENT", header_style)
        sheet2.write(row, 2, "NAMA", header_style)
        sheet2.write(row, 3, "GROUP PAJAK", header_style)
        sheet2.write(row, 4, "REKENING", header_style)
        sheet2.write(row, 5, "NIK", header_style)
        sheet2.write(row, 6, "PAYROLL CODE", header_style)
        sheet2.write(row, 7, "SECTION", header_style)
        sheet2.write(row, 8, "UNIT", header_style)
        sheet2.write(row, 9, "JABATAN", header_style)
        sheet2.write(row, 10, "NETT SALARY", header_style)

        row += 1
        idx = 0
        for pay in dtPay:
            sheet2.write(row, 0, idx + 1, int_style)
            sheet2.write(row, 1, pay.employee_id.department_id.name if pay.employee_id.department_id else "")
            sheet2.write(row, 2, pay.employee_id.name)
            sheet2.write(row, 3, pay.employee_id.tax_state + pay.employee_id.tax_state2 if pay.employee_id.tax_state else "")
            sheet2.write(row, 4, pay.employee_id.bank_account_number if pay.employee_id.bank_account_number else "")
            sheet2.write(row, 5, pay.employee_id.identification_id if pay.employee_id.identification_id else "")
            sheet2.write(row, 6, pay.employee_id.payroll_code if pay.employee_id.payroll_code else "")
            sheet2.write(row, 7, pay.employee_id.section.name if pay.employee_id.section else "")
            sheet2.write(row, 8, pay.employee_id.work_location_id.name if pay.employee_id.work_location_id else "")
            sheet2.write(row, 9, pay.employee_id.job_id.name if pay.employee_id.job_id else "")

            dtLine = self.env['hr.payslip.line'].search([
                ('slip_id','=',pay.id)], order="sequence desc")
            sheet2.write(row, 10, dtLine[0].total if dtLine else 0, float_style)

            row += 1
            idx += 1

         # GET PATH BASED ON URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        path = False
        # if 'localhost' in base_url:
        # karna server nya windos
        path = self.get_download_folder() # <- Local windows use this
        path += "\\" # <- Local windows use this
        # else:
        #     path = self.get_real_download_folder() # <- Live Prod user this

        judul = "Report Payslip " + self.company_id.name + " Periode " + str(self.date_begin.strftime('%B %Y'))
        path += judul + ".xls"
        print("Path to -> ", path)
        wb.save(path)

        # Delete another attachment application/vnd.ms-excel
        self.env['ir.attachment'].sudo().search([('mimetype','=','application/vnd.ms-excel')]).unlink()

        file = open(path, "rb")        
        datas = base64.encodestring(file.read())
        file_name = judul + ".xls"
        attachment_data = {
            'name':file_name,
            'name':file_name,
            'datas':datas,
            'res_model':"modelname",
        }
        ir_att_id = self.create_attachment(attachment_data)
        base_url = self.env['ir.config_parameter'].sudo()._get_param('web.base.url')
        download_url = '/web/content/' + str(ir_att_id) + '?download=true'

        file.close()
        os.remove(path)

        return {
            "type":"ir.actions.act_url",
            "url":str(base_url) + str(download_url),
            "target":"new"
        }

    def action_download_slip(self):
        raise ValidationError("Under Construction")
    
    def get_download_folder(self):
        from pathlib import Path
        path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))
        return path_to_download_folder

    def get_real_download_folder(self):
        path = "/opt/odoo/" # <- Server live user this
        return path

    def create_attachment(self, param):
        attachment_id = self.env['ir.attachment'].create(param)
        return attachment_id.id
