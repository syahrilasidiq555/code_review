import time
from datetime import datetime, timedelta, date

# import json
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

from random import choice
from string import digits

from odoo.osv import osv
import logging 

class hr_employee(models.Model):
    _inherit = 'hr.employee'

	# inherited
    address_home_id = fields.Many2one(string="Contact Relation")
    work_location_id = fields.Many2one(string="Unit")
    department_id = fields.Many2one('hr.department')

    # header information
    job_grade_id = fields.Many2one('hr.job.grade', string="Grade", tracking=True)
    section = fields.Many2one('hr.department', string="Section")
    # @api.onchange('department_id')
    # def _onchange_department_id(self):
    #     child = self.env['hr.department'].search([('parent_id', '=', self.department_id.id)]).ids
    #     domain = {'domain': {'section': [('id', 'in', child)]}}
    #     self.section = False
    #     return domain

    # @api.onchange('department_id')
    # def _onchange_department_id(self):
    #     for rec in self:
    #         self.section = self.get_first_parent(rec.department_id)
    
    # def get_first_parent(self, dept):
    #     if dept.parent_id:
    #         parent_id = dept.parent_id
    #         while (parent_id.parent_id):
    #             parent_id = parent_id.parent_id
    #         return parent_id.id
    #     else:
    #         return dept.id

    # citizen
    religion = fields.Selection(
        string='Religion',
        selection=[
            ('islam', 'Islam'), 
            ('kristen', 'Kristen'),
            ('katholik', 'Katholik'),
            ('budha', 'Budha'),
            ('hindu', 'Hindu'),
            ('konghucu', 'Kong Hu Cu'),
            ('others', 'Others'),
        ], tracking=True)
    other_religion = fields.Char(string="Other Religion", tracking=True)
    @api.onchange('religion')
    def _onchange_religion(self):
        self.other_religion = ""

    # dependant
    employee_family_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family')
    
    # private contact
    sim_type =  fields.Selection(
        string='Sim Type',
        selection=[
            ('a', 'A'), 
            ('b1', 'B1'),
            ('b2', 'B2'),
            ('c', 'C'),
            ('d', 'D'),
        ], tracking=True)
    sim_number = fields.Char(string="Sim Number", tracking=True)
    blood_type =  fields.Selection(
        string='Blood Type',
        selection=[
            ('a', 'A'), 
            ('o', 'O'),
            ('b', 'B'),
            ('ab', 'AB'),
        ], tracking=True)
    home_ktp = fields.Text(string='Home (KTP)', tracking=True)
    home_domisili = fields.Text(string='Home (Domisili)', tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank", tracking=True)
    bank_account_number = fields.Char(string="Account Number", tracking=True)
    iq = fields.Char(string="IQ", tracking=True)
    disc = fields.Char(string="DISC", tracking=True)
    tax_state = fields.Selection(
        string='Tax State',
        selection=[
            ('tk', 'TK'), 
            ('k', 'K'),
            ('c', 'C'),
        ])
    tax_state2 = fields.Selection(
        string='Tax State',
        selection=[
            ('1', '1'), 
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),
        ])
    

    # schedule
    working_days = fields.Selection(
        string='Working Days',
        selection=[
            ('21', '21'), 
            ('25', '25'),
        ], tracking=True)
    
    # facility & benefit
    facility = fields.Text(string="Facility", tracking=True)
    other_facility = fields.Text(string="Other Facility", tracking=True)
    bpjs_kesehatan = fields.Char(string="BPJS Kesehatan", tracking=True)
    bpjs_ketenagakerjaan = fields.Char(string="BPJS Ketenagakerjaan", tracking=True)
    
    # payroll
    payroll_code = fields.Char(string="Payroll Code", tracking=True)

    # Attendance
    attendance_exception = fields.Boolean('Attendance Exception',tracking=True)
    attendance_mode = fields.Selection([
        ('finger', 'Fingerprint Only'),
        ('geo_selfie', 'Geo & Selfie Only'),
        ('finger_geo_selfie', 'Fingerprint or Geo & Selfie'),
    ], string='Attendance Mode', default='finger_geo_selfie', required=True, tracking=True)
    fingerprint_id = fields.Char(string="Finger Print ID", tracking=True)

    # Education
    education_level = fields.Selection(string="Education Level", 
        selection=[
            ('tk','TK'),
            ('sd','SD'),
            ('smp','SMP'),
            ('sma','SMA'),
            ('d1','D1'),
            ('d2','D2'),
            ('d3','D3'),
            ('d4','D4'),
            ('s1','S1'),
            ('s2','S2'),
            ('s3','S3'),
        ], tracking=True)
    ijazah = fields.Binary(string='Ijazah', attachment=True)
    other_education_level = fields.Selection(string="Other Education", 
        selection=[
            ('kursus','Kursus'),
            ('sertifikasi','Sertifikasi'),
            ('pelatihan','Pelatihan'),
            ('seminar','Seminar'),
            ('lainnya','Lainnya'),
        ], tracking=True)
    other_ijazah = fields.Binary(string='Attachment', attachment=True)
    # other_ijazah = fields.Many2many('ir.attachment','attachment_rel','other_ijazah_id','other_ijazahattach_id', string='Attachments') 
    
    # Status
    employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type", store=True, tracking=True)
    current_start_date = fields.Date(groups="hr.group_hr_user", store=True, related="contract_id.date_start")
    current_end_date = fields.Date(groups="hr.group_hr_user", store=True, related="contract_id.date_end")
    type_id = fields.Many2one('hr.contract.type', string="Employee Category", store=True, related="contract_id.type_id")
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type", store=True, related="contract_id.contract_type_id")
    join_date = fields.Date(string="Join Date")
    end_date = fields.Date(string="End Date") # <-- ini nnti akan diimplementasikan ketika terminasi sdh clear

    # Peringatan
    surat_peringatan_line = fields.One2many('hr.surat.peringatan', 'employee_id', string='Surat Teguran')

    # def _get_domain_attendance(self):
    #     year_now = datetime.now().year
    #     date_start = datetime(year_now,1,1).date()
    #     date_end = datetime(year_now,12,31).date()

    #     domain = "[('teguran_tipe','=','terlambat'),('create_date','>=','%s'),('create_date','<=','%s')]" % (date_start.strftime('%Y-%m-%d'),date_end.strftime('%Y-%m-%d'))
    #     return domain

    attendance_terlambat_ids = fields.One2many('dym.teguran.attendance', 'employee_id', string='Notifikasi Terlambat')
    attendance_terlambat_thisyear_ids = fields.One2many('dym.teguran.attendance', string='Notifikasi Terlambat', compute="_compute_attendance_terlambat_thisyear_ids")
    

    def _compute_attendance_terlambat_thisyear_ids(self):
        for record in self:
            year_now = datetime.now().year
            date_start = datetime(year_now,1,1).date()
            date_end = datetime(year_now,12,31).date()
            domain = [
                    ('employee_id','=',record.id),
                    # ('teguran_tipe','=','terlambat'),
                    ('create_date','>=',date_start.strftime('%Y-%m-%d')),
                    ('create_date','<=',date_end.strftime('%Y-%m-%d'))
            ]
            record.attendance_terlambat_thisyear_ids = record.attendance_terlambat_ids.search(domain)

    # automatic pkwt
    def cron_create_pkwt(self):
        dt = self.env['hr.employee'].sudo().search([
            ('current_end_date','=',datetime.now().date()),
            ('contract_id.is_generate_pkwt','=',False)
        ])
        for i in dt:
            res = self.env['hr.kompensasi.pkwt'].sudo().create({
                    'employee_id': i.id,
                    'base_salary': i.contract_id.wage
                })
            if res:
                res._onchange_employee_id()

    def write(self, vals):
        res = super(hr_employee, self).write(vals)
        return res

    # For barcode 
    # PKWT = Kode divisi, bulan, tahun, no urut pertahun
    # HL = Kode unik (20/30) sebelum kode divisi
    hl = fields.Selection(string='HL', selection=[('20', '20'), ('30', '30')])
    def generate_random_barcode(self):
        for employee in self:
            # employee.barcode = '041'+"".join(choice(digits) for i in range(9))
            nik = ""
            if employee.hl: nik += employee.hl
            else: raise ValidationError("HL must be selected.")
            if employee.department_id: nik += employee.department_id.code
            else: raise ValidationError("Department must be selected.")
            if employee.join_date: nik += employee.join_date.strftime("%m") + employee.join_date.strftime("%y")
            else: raise ValidationError("Join Date must be filled.")
            nik += self.env['ir.sequence'].next_by_code('hr.employee.nik.number') or ('New')
            employee.barcode = nik

class hr_employee_family(models.Model):
    _name = 'hr.employee.family'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char(string="Name")
    family_status = fields.Selection(
        string='Hubungan Keluarga',
        selection=[
            ('ayah', 'Ayah'),
            ('ibu', 'Ibu'),
            ('istri', 'Istri'),
            ('suami', 'Suami'),
            ('mertua', 'Mertua'),
            ('kakak', 'Kakak'),
            ('adik', 'Adik'),
            ('anak', 'Anak'),
            ('lainnya', 'Lainnya'),
        ])

class hr_employee_public(models.Model):
    _inherit = 'hr.employee.public'

    job_grade_id = fields.Many2one('hr.job.grade', string="Grade", tracking=True)
    section = fields.Many2one('hr.department', string="Section")

    religion = fields.Selection(
        string='Religion',
        selection=[
            ('islam', 'Islam'), 
            ('kristen', 'Kristen'),
            ('katholik', 'Katholik'),
            ('budha', 'Budha'),
            ('hindu', 'Hindu'),
            ('konghucu', 'Kong Hu Cu'),
            ('others', 'Others'),
        ], tracking=True)
    other_religion = fields.Char(string="Other Religion", tracking=True)
    
    employee_family_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family')

    sim_type =  fields.Selection(
        string='Sim Type',
        selection=[
            ('a', 'A'), 
            ('b1', 'B1'),
            ('b2', 'B2'),
            ('c', 'C'),
            ('d', 'D'),
        ], tracking=True)
    sim_number = fields.Char(string="Sim Number", tracking=True)
    blood_type =  fields.Selection(
        string='Blood Type',
        selection=[
            ('a', 'A'), 
            ('o', 'O'),
            ('b', 'B'),
            ('ab', 'AB'),
        ], tracking=True)
    home_ktp = fields.Text(string='Home (KTP)', tracking=True)
    home_domisili = fields.Text(string='Home (Domisili)', tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank", tracking=True)
    bank_account_number = fields.Char(string="Account Number", tracking=True)
    iq = fields.Char(string="IQ", tracking=True)
    disc = fields.Char(string="DISC", tracking=True)
    tax_state = fields.Selection(
        string='Tax State',
        selection=[
            ('tk', 'TK'), 
            ('k', 'K'),
            ('c', 'C'),
        ])
    tax_state2 = fields.Selection(
        string='Tax State',
        selection=[
            ('1', '1'), 
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),
        ])
    
    working_days = fields.Selection(
        string='Working Days',
        selection=[
            ('21', '21'), 
            ('25', '25'),
        ], tracking=True)
    
    facility = fields.Text(string="Facility", tracking=True)
    other_facility = fields.Text(string="Other Facility", tracking=True)
    bpjs_kesehatan = fields.Char(string="BPJS Kesehatan", tracking=True)
    bpjs_ketenagakerjaan = fields.Char(string="BPJS Ketenagakerjaan", tracking=True)

    payroll_code = fields.Char(string="Payroll Code", tracking=True)

    attendance_exception = fields.Boolean('Attendance Exception',tracking=True)
    attendance_mode = fields.Selection([
        ('finger', 'Fingerprint Only'),
        ('geo_selfie', 'Geo & Selfie Only'),
        ('finger_geo_selfie', 'Fingerprint or Geo & Selfie'),
    ], string='Attendance Mode', default='finger_geo_selfie', required=True, tracking=True)
    fingerprint_id = fields.Char(string="Finger Print ID", tracking=True)

    education_level = fields.Selection(string="Education Level", 
        selection=[
            ('tk','TK'),
            ('sd','SD'),
            ('smp','SMP'),
            ('sma','SMA'),
            ('d1','D1'),
            ('d2','D2'),
            ('d3','D3'),
            ('d4','D4'),
            ('s1','S1'),
            ('s2','S2'),
            ('s3','S3'),
        ], tracking=True)
    # ijazah = fields.Binary(string='Ijazah', attachment=True)
    other_education_level = fields.Selection(string="Other Education", 
        selection=[
            ('kursus','Kursus'),
            ('sertifikasi','Sertifikasi'),
            ('pelatihan','Pelatihan'),
            ('seminar','Seminar'),
            ('lainnya','Lainnya'),
        ], tracking=True)
    # other_ijazah = fields.Binary(string='Attachment', attachment=True)

    employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type", store=True, tracking=True)
    current_start_date = fields.Date(groups="hr.group_hr_user", store=True)
    current_end_date = fields.Date(groups="hr.group_hr_user", store=True)
    type_id = fields.Many2one('hr.contract.type', string="Employee Category", store=True)
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type", store=True)
    join_date = fields.Date(string="Join Date")
    end_date = fields.Date(string="End Date")

    surat_peringatan_line = fields.One2many('hr.surat.peringatan', 'employee_id', string='Surat Teguran')

    attendance_terlambat_ids = fields.One2many('dym.teguran.attendance', 'employee_id', string='Notifikasi Terlambat')
    attendance_terlambat_thisyear_ids = fields.One2many('dym.teguran.attendance', string='Notifikasi Terlambat', compute="_compute_attendance_terlambat_thisyear_ids")

    hl = fields.Selection(string='HL', selection=[('20', '20'), ('30', '30')])