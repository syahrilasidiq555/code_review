# from attr import field
from unicodedata import category
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


from datetime import datetime
from dateutil.relativedelta import relativedelta

def checkList(list):
    element = list[0]
    check = True
    # Comparing each element with first item
    for item in list:
        if element != item:
            check = False
            break
    return check

class ResPartner(models.Model):
    _inherit = 'res.partner'

    parent_id = fields.Many2one(string='Parent')
    is_jenazah = fields.Boolean(string="Jenazah", default=False, store=True)
    is_penanggungjawab = fields.Boolean(string="Penanggung Jawab", default=False, store=True)

    kewarganegaraan = fields.Selection([
        ('WNI', 'Warga Negara Indonesia (WNI)'),
        ('WNA', 'Warga Negara Asing (WNA)'),
    ], string='Kewarganegaraan', tracking=True)

    kategori_usia = fields.Selection([
        ('anak', 'Anak'),
        ('dewasa', 'Dewasa'),
    ], string='Kategori Usia', tracking=True)
    
    no_passport = fields.Char(string='No. Passport', tracking=True)
    no_ktp = fields.Char(string='No. Identitas', tracking=True)
    no_npwp = fields.Char(string='No. NPWP', tracking=True)

    @api.constrains('no_passport')
    def _constrains_no_passport(self):
        for record in self:
            if record.no_passport:
                # if len(record.no_passport) != 16:
                #     raise ValidationError("No. KTP yang diinput harus 16 digit!\n\nNama: {partner_name}\nTotal digit : {digit}".format(
                #         partner_name = record.name,
                #         digit=len(record.no_passport)
                #     ))

                partner = self.env[self._name].search([
                    ('id','!=',record.id),
                    ('no_passport','=',record.no_passport)
                ])
                if partner:
                    message = "No. Passport yang diinput telah digunakan sebelumnya oleh {name}".format(
                        name=partner[0].name
                    )
                    raise ValidationError(message)

    @api.constrains('no_ktp')
    def _constrains_no_ktp(self):
        for record in self:
            if record.no_ktp:
                # for char in record.no_ktp:
                #     ## ord(chr) returns the ascii value
                #     ## CHECKING FOR UPPER CASE
                #     only_number = ""
                #     if ord(char) >= 48 and ord(char) <= 57:
                #         only_number += char

                #     if record.no_ktp != only_number:
                #         raise ValidationError("No. Identitas hanya boleh diisi dengan angka!\n\nNama : {partner_name}\nNo Identitas : {identitas}".format(
                #         partner_name = record.name,
                #         identitas=record.no_ktp
                #     ))

                if not record.no_ktp.isnumeric():
                    raise ValidationError("No. Identitas hanya boleh diisi dengan angka!\n\nNama : {partner_name}\nNo Identitas : {identitas}".format(
                        partner_name = record.name,
                        identitas=record.no_ktp
                    ))
                   
                if len(record.no_ktp) != 16:
                    raise ValidationError("No. Identitas yang diisi harus 16 digit!\n\nNama : {partner_name}\nTotal digit : {digit}".format(
                        partner_name = record.name,
                        digit=len(record.no_ktp)
                    ))

                partner = self.env[self._name].search([
                    ('id','!=',record.id),
                    ('no_ktp','=',record.no_ktp)
                ])
                if partner:
                    message = "No. Identitas yang diisi telah digunakan sebelumnya oleh {name}".format(
                        name=partner[0].name
                    )
                    raise ValidationError(message)
    
    @api.constrains('no_npwp')
    def _constrains_no_npwp(self):
        for record in self:
            if record.no_npwp:
                if len(record.no_npwp) != 15:
                    raise ValidationError("No. NPWP yang diinput harus 15 digit!\n\nNama: {partner_name}\nTotal digit : {digit}".format(
                        partner_name = record.name,
                        digit=len(record.no_npwp)
                    ))
                
                partner = self.env[self._name].search([
                    ('id','!=',record.id),
                    ('no_npwp','=',record.no_npwp)
                ])
                if partner:
                    message = "No. NPWP yang diinput telah digunakan sebelumnya oleh {name}".format(
                        name=partner[0].name
                    )
                    raise ValidationError(message)
    
    # @api.constrains('phone')
    # def _constrains_partner_phone(self):
    #     for record in self:
    #         if record.phone:
    #             if not record.phone.isnumeric():
    #                 raise ValidationError("Nomor telepon hanya boleh diisi dengan angka!")
    
    tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    tanggal_kematian = fields.Datetime(string='Tanggal Kematian', tracking=True)

    @api.constrains('tanggal_lahir','tanggal_kematian')
    def _constrains_tanggal_lahir_kematian(self):
        for record in self:
            if record.tanggal_lahir and record.tanggal_kematian and record.tanggal_lahir > record.tanggal_kematian.date():
                message = "Tanggal lahir tidak boleh melebihi tanggal kematian\n\n"
                message += "Tanggal Lahir : %s\n" % record.tanggal_lahir.strftime("%d/%m/%Y")
                message += "Tanggal Kematian : %s" % record.tanggal_kematian.strftime("%d/%m/%Y")
                raise UserError(message)

    usia = fields.Integer(compute='_compute_usia', string='Usia', store=True, tracking=True)
    @api.depends('tanggal_lahir','tanggal_kematian')
    def _compute_usia(self):
        for record in self:
            usia = 0
            if record.tanggal_lahir and record.tanggal_kematian:
                usia = relativedelta(record.tanggal_kematian, record.tanggal_lahir).years
            record.usia = usia
    
    tujuan = fields.Selection([
        ('kremasi', 'Kremasi'),
        ('pemakaman', 'Pemakaman'),
        ('columbarium', 'Columbarium'),
        ('rumah', 'Rumah'),
        ('transit', 'Transit'),
        ('luar kota', 'Luar Kota'),
        ('internasional', 'Internasional'),
    ], string='Tujuan', tracking=True)
    tanggal_keluar = fields.Datetime('Tanggal Keluar')

    @api.constrains('tanggal_kedatangan','tanggal_keluar')
    def _constrains_tanggal_tanggal_datang_keluar(self):
        for record in self:
            if record.tanggal_kedatangan and record.tanggal_keluar and record.tanggal_kedatangan > record.tanggal_keluar:
                message = "Tanggal Kedatangan tidak boleh melebihi tanggal Keluar\n\n"
                message += "Tanggal Kedatangan : %s\n" % record.tanggal_kedatangan.strftime("%d %b %Y %H:%S:%M")
                message += "Tanggal Kematian : %s" % record.tanggal_keluar.strftime("%d %b %Y %H:%S:%M")
                raise UserError(message)

    # kremasi
    tujuan_kremasi = fields.Selection([
        ('disimpan', 'Disimpan'),
        ('larung', 'Dilarung'),
        ('simpan_larung', 'Dilarung dan Disimpan'),
        ('pemakaman', 'Dimakamkan'),
        ('bawa_pulang', 'Dibawa Pulang'),
        ('dibawa_keluar', 'Dibawa ke Luar daerah / Luar Negeri'),
        # ('columbarium_lain', 'Dibawa ke Columbarium Lain'),
    ], string='Tujuan Abu Jenazah', tracking=True)
    jadwal_kremasi = fields.Datetime(string='Jadwal Kremasi', tracking=True)
    # kremasi - kalau dilarung
    jadwal_transportasi = fields.Datetime(string='Jadwal Transportasi', tracking=True)
    tujuan_larung = fields.Char(string='Tujuan Larung', tracking=True)
    larung_vendor_id = fields.Many2one('res.partner', string='Vendor', domain=[('is_vendor','=',True)])
    tujuan_simpan = fields.Selection([
        ('rumah', 'Rumah'),
        ('columbarium', 'Columbarium RDC'),
        ('columbarium_lain', 'Columbarium Lain'),
    ], string='Tujuan Simpan',tracking=True)


    # pemakaman
    jenis_transportasi = fields.Selection([
        ('RDC', 'Kendaraan RDC'),
        ('Vendor', 'Kendaraan Pihak Ketiga'),
        ('luar RDC', 'Kendaraan Mobil Dinas atau Pribadi'),
    ], string='Kendaraan')

    def _get_transportasi_id_domain(self):
        categ_transport_id = self.env.ref('custom_sale_order.categ_transportasi_jenazah')
        # return [('categ_id','=', categ_transport_id.id),('qty_available','>=',1)]
        return [('categ_id','=', categ_transport_id.id)]
    transportasi_id = fields.Many2one('product.product', string='Mobil Jenazah', domain=_get_transportasi_id_domain)

    transportasi = fields.Char(string='Mobil Jenazah', tracking=True)
    tanggal_pemakaman = fields.Datetime(string='Tanggal Pemakaman', tracking=True)
    tujuan_pemakaman = fields.Selection([
        ('jabodetabek', 'Jabodetabek'),
        ('luar jabodetabek', 'Luar Jabodetabek'),
        # ('luar kota', 'Luar Kota'),
        ('internasional', 'Internasional'),
    ], string='Lokasi Pemakaman', tracking=True)
    jabodetabek_pemakaman_id = fields.Many2one('res.pemakaman', string='Tempat Pemakaman', domain="[('daerah','=','jabodetabek')]", context="{'default_daerah':'jabodetabek'}")
    luar_jabodetabek_pemakaman_id = fields.Many2one('res.pemakaman', string='Tempat Pemakaman', domain="[('daerah','=','luar jabodetabek')]", context="{'default_daerah':'luar jabodetabek'}")

    # columbarium
    type_columbarium = fields.Selection([
        ('baru', 'Baru'),
        ('perpanjang', 'Perpanjang'),
    ], string='Type Columbarium', tracking=True)
    asal_abu = fields.Selection([
        ('RDC', 'Rumah Duka Carolus'),
        ('luar', 'Luar Rumah Duka Carolus'),
    ], string='Asal Abu', tracking=True)

    # rumah
    alamat_disemayamkan = fields.Text('Alamat Disemayamkan')

    # Luar kota
    kota_tujuan = fields.Char('Kota Tujuan')

    # luar negeri
    negara_tujuan_id = fields.Many2one('res.country', string='Negara Tujuan')

    # document
    surat_kematian = fields.Binary(string='Surat Kematian', attachment=True, store=True, tracking=True)
    surat_kematian_filename = fields.Char(string='Filename Surat Kematian', tracking=True)
    surat_kematian_web_url = fields.Char(compute='_compute_surat_kematian_web_url', string='URL Surat Kematian', store=True)
    @api.depends('surat_kematian','surat_kematian_filename')
    def _compute_surat_kematian_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            surat_kematian_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'surat_kematian'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                surat_kematian_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.surat_kematian_web_url = surat_kematian_web_url

    kartu_keluarga = fields.Binary(string='Kartu Keluarga', attachment=True, store=True, tracking=True)
    kartu_keluarga_filename = fields.Char(string='Filename Kartu Keluarga', tracking=True)
    kartu_keluarga_web_url = fields.Char(compute='_compute_kartu_keluarga_web_url', string='URL Kartu Keluarga', store=True)
    @api.depends('kartu_keluarga','kartu_keluarga_filename')
    def _compute_kartu_keluarga_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            kartu_keluarga_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'kartu_keluarga'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                kartu_keluarga_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.kartu_keluarga_web_url = kartu_keluarga_web_url

    surat_keterangan_kremasi = fields.Binary(string='Surat Keterangan Kremasi', attachment=True, store=True)
    surat_keterangan_kremasi_filename = fields.Char(string='Filename Surat Keterangan Kremasi', tracking=True)
    surat_keterangan_kremasi_web_url = fields.Char(compute='_compute_surat_keterangan_kremasi_web_url', string='URL Surat keterangan Kremasi', store=True)
    @api.depends('surat_keterangan_kremasi','surat_keterangan_kremasi_filename')
    def _compute_surat_keterangan_kremasi_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            surat_keterangan_kremasi_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'surat_keterangan_kremasi'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                surat_keterangan_kremasi_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.surat_keterangan_kremasi_web_url = surat_keterangan_kremasi_web_url

    rekam_medis = fields.Binary(string='Rekam Medis', attachment=True, store=True, tracking=True)
    rekam_medis_filename = fields.Char(string='Filename Rekam Medis', tracking=True)
    rekam_medis_web_url = fields.Char(compute='_compute_rekam_medis_web_url', string='URL Rekam Medis', store=True)
    @api.depends('rekam_medis','rekam_medis_filename')
    def _compute_rekam_medis_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rekam_medis_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'rekam_medis'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                rekam_medis_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.rekam_medis_web_url = rekam_medis_web_url

    izin_angkut = fields.Binary(string='Izin Angkut dari Kelurahan', attachment=True, store=True, tracking=True)
    izin_angkut_filename = fields.Char(string='Filename Izin Angkut dari Kelurahan', tracking=True)
    izin_angkut_web_url = fields.Char(compute='_compute_izin_angkut_web_url', string='URL Izin Angkut dari Kelurahan', store=True)
    @api.depends('izin_angkut','izin_angkut_filename')
    def _compute_izin_angkut_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            izin_angkut_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'izin_angkut'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                izin_angkut_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.izin_angkut_web_url = izin_angkut_web_url

    sertifikat_formalin = fields.Binary(string='Sertifikat Formalin', attachment=True, store=True, tracking=True)
    sertifikat_formalin_filename = fields.Char(string='Filename Sertifikat Formalin', tracking=True)
    sertifikat_formalin_web_url = fields.Char(compute='_compute_sertifikat_formalin_web_url', string='URL Sertifikat Formalin', store=True)
    @api.depends('sertifikat_formalin','sertifikat_formalin_filename')
    def _compute_sertifikat_formalin_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            sertifikat_formalin_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'sertifikat_formalin'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                sertifikat_formalin_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.sertifikat_formalin_web_url = sertifikat_formalin_web_url

    izin_tahan_jenazah = fields.Binary(string='Izin Tahan Jenazah', attachment=True, store=True, tracking=True)
    izin_tahan_jenazah_filename = fields.Char(string='Filename Izin Tahan jenazah', tracking=True)
    izin_tahan_jenazah_web_url = fields.Char(compute='_compute_izin_tahan_jenazah_web_url', string='URL Izin Tahan Jenazah', store=True)
    @api.depends('izin_tahan_jenazah','izin_tahan_jenazah_filename')
    def _compute_izin_tahan_jenazah_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            izin_tahan_jenazah_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'izin_tahan_jenazah'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                izin_tahan_jenazah_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.izin_tahan_jenazah_web_url = izin_tahan_jenazah_web_url

    surat_berita_acara_kremasi = fields.Binary(string='Surat Berita Acara Kremasi', attachment=True, store=True, tracking=True)
    surat_berita_acara_kremasi_filename = fields.Char(string='Filename Surat Berita Acara Kremasi', tracking=True)
    surat_berita_acara_kremasi_web_url = fields.Char(compute='_compute_surat_berita_acara_kremasi_web_url', string='URL Surat Berita Acara Kremasi', store=True)
    @api.depends('surat_berita_acara_kremasi','surat_berita_acara_kremasi_filename')
    def _compute_surat_berita_acara_kremasi_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            surat_berita_acara_kremasi_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'surat_berita_acara_kremasi'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                surat_berita_acara_kremasi_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.surat_berita_acara_kremasi_web_url = surat_berita_acara_kremasi_web_url

    surat_permohonan_pengawetan_jenazah = fields.Binary(string='Surat Pernyataan Permohonan Pengawetan Jenazah', attachment=True, store=True, tracking=True)
    surat_permohonan_pengawetan_jenazah_filename = fields.Char(string='Filename Surat Pernyataan Permohonan Pengawetan Jenazah', tracking=True)
    surat_permohonan_pengawetan_jenazah_web_url = fields.Char(compute='_compute_surat_permohonan_pengawetan_jenazah_web_url', string='URL Surat Pernyataan Permohonan Pengawetan Jenazah', store=True)
    @api.depends('surat_permohonan_pengawetan_jenazah','surat_permohonan_pengawetan_jenazah_filename')
    def _compute_surat_permohonan_pengawetan_jenazah_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            surat_permohonan_pengawetan_jenazah_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'surat_permohonan_pengawetan_jenazah'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                surat_permohonan_pengawetan_jenazah_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.surat_permohonan_pengawetan_jenazah_web_url = surat_permohonan_pengawetan_jenazah_web_url

    
    ktp_almarhum = fields.Binary(string='KTP Almarhum', attachment=True, store=True, tracking=True)
    ktp_almarhum_filename = fields.Char(string='Filename KTP Almarhum', tracking=True)
    ktp_almarhum_web_url = fields.Char(compute='_compute_ktp_almarhum_web_url', string='URL KTP Almarhum', store=True)
    @api.depends('ktp_almarhum','ktp_almarhum_filename')
    def _compute_ktp_almarhum_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ktp_almarhum_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'ktp_almarhum'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                ktp_almarhum_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.ktp_almarhum_web_url = ktp_almarhum_web_url
    
    ktp_penanggungjawab = fields.Binary(string='KTP Penanggung Jawab', attachment=True, store=True, tracking=True)
    ktp_penanggungjawab_filename = fields.Char(string='Filename KTP Penanggung Jawab', tracking=True)
    ktp_penanggungjawab_web_url = fields.Char(compute='_compute_ktp_penanggungjawab_web_url', string='URL KTP Penanggung Jawab', store=True)
    @api.depends('ktp_penanggungjawab','ktp_penanggungjawab_filename')
    def _compute_ktp_penanggungjawab_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ktp_penanggungjawab_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'ktp_penanggungjawab'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                ktp_penanggungjawab_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.ktp_penanggungjawab_web_url = ktp_penanggungjawab_web_url
    
    ktp_pemberi_kuasa = fields.Binary(string='KTP Pemberi Kuasa', attachment=True, store=True, tracking=True)
    ktp_pemberi_kuasa_filename = fields.Char(string='Filename KTP Pemberi Kuasa', tracking=True)
    ktp_pemberi_kuasa_web_url = fields.Char(compute='_compute_ktp_pemberi_kuasa_web_url', string='URL KTP Pemberi Kuasa', store=True)
    @api.depends('ktp_pemberi_kuasa','ktp_pemberi_kuasa_filename')
    def _compute_ktp_pemberi_kuasa_web_url(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ktp_pemberi_kuasa_web_url = ""
            domain = [
                ('res_model', '=', record._name),
                ('res_field', '=', 'ktp_pemberi_kuasa'),
                ('res_id', '=', record.id),
            ]
            attachment = self.env['ir.attachment'].search(domain)
            if attachment and base_url:
                ktp_pemberi_kuasa_web_url = "{base_url}{website_url}".format(
                    base_url = base_url,
                    website_url = attachment.website_url
                )
            record.ktp_pemberi_kuasa_web_url = ktp_pemberi_kuasa_web_url

    # tambahan informasi field
    jenis_kelamin = fields.Selection([
        ('perempuan', 'Perempuan'),
        ('laki-laki', 'Laki-laki'),
    ], string='Jenis Kelamin')
    agama = fields.Selection([
        ('islam', 'Islam'),
        ('protestan', 'Kristen Protestan'),
        ('katolik', 'Kristen Katolik'),
        ('hindu', 'Hindu'),
        ('buddha', 'Buddha'),
        ('lainnya', 'Lainnya')
    ], string='Agama')
    penyakit = fields.Char(string='Penyakit/Gangguan', tracking=True)
    tanggal_kedatangan = fields.Datetime(string='Tanggal Kedatangan', tracking=True)
    asal = fields.Char(string='Asal', tracking=True)
    pelayanan = fields.Char(string='Pelayanan', tracking=True)
    no_pol_kendaraan = fields.Char(string='No Pol Kendaraan', tracking=True)
    # ruangan_id = fields.Many2one('product.product', string='Ruangan', tracking=True, readonly=True)
    # paket_id = fields.Many2one('product.template', string='Paket', tracking=True, readonly=True, domain="[('ni_is_product_pack','=',True)]")
    ruangan_id = fields.Many2one('product.product', string='Ruangan', compute='_compute_ruangan_paket_status_semayam', store=True)
    paket_id = fields.Many2one('product.template', string='Paket', compute='_compute_ruangan_paket_status_semayam', store=True)

    is_still_semayam = fields.Boolean(compute='_compute_ruangan_paket_status_semayam', string='Masih Semayam?', store=True)
    
    @api.depends('sale_order_count','sale_order_ids','sale_order_ids.rental_status','sale_order_ids.order_line','sale_order_ids.order_line.qty_delivered','sale_order_ids.invoice_ids','sale_order_ids.invoice_ids.state')
    def _compute_ruangan_paket_status_semayam(self):
        for record in self:
            ruangan_id = None
            paket_id = None
            is_still_semayam = False
            sale_ids = [x.id for x in record.sale_order_ids.filtered(lambda x: x.ruang_semayam_id or x.paket_id)]
            if sale_ids:
                last_sale_id = max(sale_ids)
                
                sale_order = self.env['sale.order'].browse(last_sale_id)
                if sale_order:
                    # set ruangan
                    ruangan_id = sale_order.ruang_semayam_id if sale_order.ruang_semayam_id else ruangan_id
                    # set paket
                    paket_id = sale_order.paket_id if sale_order.paket_id else paket_id
                    
                    # get produk ruang semayam yang sudah di pickup (untuk menentukan kalau sedang dalam semayam)
                    ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
                    ruang_semayam_pickedup_rentals = self.env['sale.rental.schedule'].search([
                        ('order_id','=',sale_order.id),
                        ('product_id.categ_id','=',ruang_semayam_category_id.id),
                        ('report_line_status','=','pickedup')
                    ])
                    # get invoice belum dibayar
                    # invoice_not_paid = sale_order.invoice_ids.filtered(lambda x: x.state in ['draft','posted'] and x.payment_state in ['not_paid','partial'])
                    
                    # set ruang semayam status
                    # is_still_semayam = True if ruang_semayam_pickedup_rentals or invoice_not_paid else False
                    is_still_semayam = True if ruang_semayam_pickedup_rentals else False

            record.ruangan_id = ruangan_id
            record.paket_id = paket_id
            record.is_still_semayam = is_still_semayam


    # last_sale_invoice_status = fields.Selection([
    #     ('none', 'None'),
    #     ('draft', 'Draft'),
    #     ('posted', 'Posted'),
    #     ('cancel', 'Cancel'),
    # ], string='Last sale Invoice Status', compute='_compute_ruangan_paket_id', store=True)

    # @api.depends('sale_order_count','sale_order_ids','sale_order_ids.invoice_ids','sale_order_ids.invoice_ids.state')
    # def _compute_ruangan_paket_id(self):
    #     for record in self:
    #         ruangan_id = None
    #         paket_id = None
    #         last_sale_invoice_status = 'none'
    #         so_id = 0
    #         sale_semayam = record.sale_order_ids.filtered(lambda x: x.ruang_semayam_id or x.paket_id)
    #         for sale in sale_semayam:
    #             if sale.id > so_id:
    #                 so_id = sale.id
    #                 # set ruangan
    #                 ruangan_id = sale.ruang_semayam_id if sale.ruang_semayam_id else ruangan_id
    #                 # set paket
    #                 paket_id = sale.paket_id if sale.paket_id else paket_id
    #                 # set last sale invoice all status
    #                 list_inv_status = []
    #                 for inv in sale.invoice_ids.filtered(lambda x: x.state != 'cancel'):
    #                     list_inv_status.append(inv.state)
    #                 if list_inv_status and checkList(list_inv_status):
    #                     last_sale_invoice_status = list_inv_status[0]
    #                 elif list_inv_status and not checkList(list_inv_status):
    #                     last_sale_invoice_status = 'draft'

    #         record.ruangan_id = ruangan_id
    #         record.paket_id = paket_id
    #         record.last_sale_invoice_status = last_sale_invoice_status

    peti_id = fields.Many2one('product.product', string='Peti', tracking=True, readonly=True)
    # is_transit = fields.Boolean(string='Transit', tracking=True)
    tanggal_terima_abu = fields.Datetime(string='Tanggal Terima Abu Jenazah', tracking=True)
    jadwal_ibadah = fields.Datetime(string='Jadwal Ibadah', tracking=True)
    nama_pemuka_agama = fields.Char(string='Nama Pemuka Agama', tracking=True)
    paroki = fields.Char(string='Paroki', tracking=True)
    tanggal_keberangkatan = fields.Datetime(string='Tanggal Keberangkatan', tracking=True)
    keterangan = fields.Text(string='Keterangan', tracking=True)

    penanggungjawab = fields.Char(compute='_compute_penanggungjawab', string='Penanggung Jawab', store=True)
    
    @api.depends('is_jenazah','child_ids')
    def _compute_penanggungjawab(self):
        for record in self:
            penanggungjawab = ''
            if record.is_jenazah and record.child_ids:
                for child in record.child_ids:
                    penanggungjawab += "%s, " % child.name
            record.penanggungjawab = penanggungjawab[:-2] if penanggungjawab else ''

    def name_get(self):
        res_names = super(ResPartner, self).name_get()
        if not self._context.get('only_name'):
            return res_names
        elif self.env.context.get('only_name', False):
            result = []
            for record in self:
                name = record.name
                result.append((record.id, name))
            return result