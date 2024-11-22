from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


import secrets
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


from babel.dates import format_date, format_datetime, format_time
from num2words import num2words
from googletrans import Translator

class CustomerFormWebsite(models.Model):
    _name = "customer.form.website"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Customer Form Website"
    _order = "name desc"

    name = fields.Char('Name')
    date = fields.Date('Tanggal', required=True, default=datetime.now().date())

    token = fields.Char(string='Token')
    url_form = fields.Char(compute='_compute_url_form', string='URL Form')
    
    @api.depends('token')
    def _compute_url_form(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.url_form = '{base_url}/customer-form/{token}'.format(
                base_url = base_url,
                token = record.token
            )


    customer_id = fields.Many2one('res.partner', string='Penanggung Jawab')
    customer2_id = fields.Many2one('res.partner', string='Penanggung Jawab 2')
    jenazah_id = fields.Many2one('res.partner', string='Jenazah')

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_id_state = fields.Selection(related="sale_order_id.state")
    
    status = fields.Selection([
        ('belum_diisi', 'Belum Diisi'),
        ('sudah_diisi', 'Sudah Diisi'),
    ], string='Status', default='belum_diisi', compute='_compute_status', store=True)
    @api.depends('customer_id','jenazah_id','customer2_id')
    def _compute_status(self):
        for record in self:
            record.status = 'belum_diisi'
            if record.customer_id and record.jenazah_id:
                record.status = 'sudah_diisi'


    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    # inputan penanggung jawab
    penanggungjawab_name = fields.Char(related="customer_id.name", readonly=False, string='Nama')
    penanggungjawab_no_ktp = fields.Char(related="customer_id.no_ktp", readonly=False)

    @api.onchange('penanggungjawab_no_ktp')
    def _onchange_penanggungjawab_no_ktp(self):
        for record in self:
            if record.penanggungjawab_no_ktp:
                no_ktp = record.penanggungjawab_no_ktp
                partner = self.env['res.partner'].search([('no_ktp','=',record.penanggungjawab_no_ktp),('is_jenazah','=',False)], limit=1)
                if partner:
                    record.customer_id = partner
                else:
                    if record.customer_id and not record._origin.id:
                        record.customer_id = None
                        record.penanggungjawab_no_ktp = no_ktp

    penanggungjawab_no_npwp = fields.Char(related="customer_id.no_npwp", readonly=False, string='No. NPWP')
    @api.onchange('penanggungjawab_no_npwp')
    def _onchange_penanggungjawab_no_npwp(self):
        for record in self:
            if record.penanggungjawab_no_npwp:
                record.penanggungjawab_l10n_id_pkp = True

    penanggungjawab_l10n_id_pkp = fields.Boolean(related="customer_id.l10n_id_pkp", readonly=False)
    penanggungjawab_phone = fields.Char(related="customer_id.phone", readonly=False, string='No. Telepon')
    penanggungjawab_street = fields.Char(related="customer_id.street", readonly=False, string='Alamat')
    penanggungjawab_city = fields.Char(related="customer_id.city", readonly=False, string='Kota')
    penanggungjawab_zip = fields.Char(related="customer_id.zip", readonly=False, string='Kode Pos')
    penanggungjawab_state_id = fields.Many2one(related="customer_id.state_id", readonly=False, comodel_name='res.country.state', string='Provinsi', domain="[('country_id','=?',penanggungjawab_country_id)]")
    penanggungjawab_country_id = fields.Many2one(related="customer_id.country_id", readonly=False, comodel_name='res.country', string='Country', default=100)

    # inputan penanggung jawab 2
    penanggungjawab2_name = fields.Char(related="customer2_id.name", readonly=False, string='Nama')
    penanggungjawab2_no_ktp = fields.Char(related="customer2_id.no_ktp", readonly=False)
    
    @api.onchange('penanggungjawab2_no_ktp')
    def _onchange_penanggungjawab2_no_ktp(self):
        for record in self:
            if record.penanggungjawab2_no_ktp:
                no_ktp = record.penanggungjawab2_no_ktp
                partner = self.env['res.partner'].search([('no_ktp','=',record.penanggungjawab2_no_ktp),('is_jenazah','=',False)], limit=1)
                if partner:
                    record.customer2_id = partner
                else:
                    if record.customer2_id and not record._origin.id:
                        record.customer2_id = None
                        record.penanggungjawab2_no_ktp = no_ktp

    penanggungjawab2_no_npwp = fields.Char(related="customer2_id.no_npwp", readonly=False, string='No. NPWP')
    penanggungjawab2_phone = fields.Char(related="customer2_id.phone", readonly=False, string='No. Telepon')
    penanggungjawab2_street = fields.Char(related="customer2_id.street", readonly=False, string='Alamat')
    penanggungjawab2_city = fields.Char(related="customer2_id.city", readonly=False, string='Kota')
    penanggungjawab2_zip = fields.Char(related="customer2_id.zip", readonly=False, string='Kode Pos')
    penanggungjawab2_state_id = fields.Many2one(related="customer2_id.state_id", readonly=False, comodel_name='res.country.state', string='Provinsi', domain="[('country_id','=?',penanggungjawab2_country_id)]")
    penanggungjawab2_country_id = fields.Many2one(related="customer2_id.country_id", readonly=False, comodel_name='res.country', string='Country', default=100)

    # inputan almarhum
    almarhum_name = fields.Char(related="jenazah_id.name", readonly=False, string='Nama')
    almarhum_kewarganegaraan = fields.Selection(related="jenazah_id.kewarganegaraan", readonly=False)

    almarhum_kategori_usia = fields.Selection(related="jenazah_id.kategori_usia", readonly=False)

    almarhum_no_passport = fields.Char(related="jenazah_id.no_passport", readonly=False)
    almarhum_no_ktp = fields.Char(related="jenazah_id.no_ktp", readonly=False)
    almarhum_jenis_kelamin = fields.Selection(related="jenazah_id.jenis_kelamin", readonly=False)
    almarhum_agama = fields.Selection(related="jenazah_id.agama", readonly=False)
    almarhum_tanggal_lahir = fields.Date(related="jenazah_id.tanggal_lahir", readonly=False, string='Tanggal Lahir')
    almarhum_tanggal_kematian = fields.Datetime(related="jenazah_id.tanggal_kematian", readonly=False, string='Tanggal Kematian')
    almarhum_usia = fields.Integer(compute='_compute_usia', string='Usia')
    @api.depends('almarhum_tanggal_lahir','almarhum_tanggal_kematian')
    def _compute_usia(self):
        for record in self:
            almarhum_usia = 0
            if record.almarhum_tanggal_lahir and record.almarhum_tanggal_kematian:
                almarhum_usia = relativedelta(record.almarhum_tanggal_kematian, record.almarhum_tanggal_lahir).years
            record.almarhum_usia = almarhum_usia
    
    almarhum_tanggal_pemakaman = fields.Datetime(related="jenazah_id.tanggal_pemakaman", readonly=False, string='Tanggal Pemakaman')
    
    almarhum_street = fields.Char(related="jenazah_id.street", readonly=False, string='Alamat')
    almarhum_city = fields.Char(related="jenazah_id.city", readonly=False, string='Kota')
    almarhum_zip = fields.Char(related="jenazah_id.zip", readonly=False, string='Kode Pos')
    almarhum_state_id = fields.Many2one(related="jenazah_id.state_id", readonly=False, comodel_name='res.country.state', string='Provinsi', domain="[('country_id','=?',almarhum_country_id)]")
    almarhum_country_id = fields.Many2one(related="jenazah_id.country_id", readonly=False, comodel_name='res.country', string='Country', default=100)


    almarhum_tujuan = fields.Selection(related="jenazah_id.tujuan", readonly=False)
    almarhum_tujuan_kremasi = fields.Selection(related="jenazah_id.tujuan_kremasi", readonly=False)
    almarhum_hospital_id = fields.Many2one(related="jenazah_id.hospital_id", readonly=False)
    
    # kremasi
    almarhum_jadwal_kremasi = fields.Datetime(related="jenazah_id.jadwal_kremasi", readonly=False)
    almarhum_tujuan_larung = fields.Char(related="jenazah_id.tujuan_larung", readonly=False)
    almarhum_larung_vendor_id = fields.Many2one(related="jenazah_id.larung_vendor_id", readonly=False)
    almarhum_larung_sale_order_line_id = fields.Many2one('sale.order.line', string='Larung sale order line')
    almarhum_tujuan_simpan = fields.Selection(related="jenazah_id.tujuan_simpan", readonly=False)

    # pemakaman
    almarhum_jadwal_transportasi = fields.Datetime(related="jenazah_id.jadwal_transportasi", readonly=False)
    almarhum_jenis_transportasi = fields.Selection(related="jenazah_id.jenis_transportasi", readonly=False)
    almarhum_transportasi_id = fields.Many2one(related="jenazah_id.transportasi_id", readonly=False)
    almarhum_transportasi_sale_order_line_id = fields.Many2one('sale.order.line', string='Transportasi sale order line')
    almarhum_transportasi = fields.Char(related="jenazah_id.transportasi", readonly=False)
    almarhum_tujuan_pemakaman = fields.Selection(related="jenazah_id.tujuan_pemakaman", readonly=False)
    almarhum_jabodetabek_pemakaman_id = fields.Many2one(related="jenazah_id.jabodetabek_pemakaman_id", readonly=False)
    almarhum_luar_jabodetabek_pemakaman_id = fields.Many2one(related="jenazah_id.luar_jabodetabek_pemakaman_id", readonly=False)

    # columbarium
    almarhum_type_columbarium = fields.Selection(related="jenazah_id.type_columbarium", readonly=False)
    almarhum_asal_abu = fields.Selection(related="jenazah_id.asal_abu", readonly=False)

    # transit
    almarhum_tanggal_keluar = fields.Datetime(related="jenazah_id.tanggal_keluar", readonly=False)

    @api.onchange('almarhum_tanggal_kedatangan','almarhum_tanggal_keluar')
    def _constrains_tanggal_tanggal_datang_keluar(self):
        for record in self:
            if record.almarhum_tanggal_kedatangan and record.almarhum_tanggal_keluar and record.almarhum_tanggal_kedatangan > record.almarhum_tanggal_keluar:
                message = "Tanggal Kedatangan tidak boleh melebihi tanggal Keluar\n\n"
                message += "Tanggal Kedatangan : %s\n" % record.almarhum_tanggal_kedatangan.strftime("%d %b %Y %H:%S:%M")
                message += "Tanggal Kematian : %s" % record.almarhum_tanggal_keluar.strftime("%d %b %Y %H:%S:%M")
                raise UserError(message)

    # rumah
    almarhum_alamat_disemayamkan = fields.Text(related="jenazah_id.alamat_disemayamkan", readonly=False)

    # Luar kota
    almarhum_kota_tujuan = fields.Char(related="jenazah_id.kota_tujuan", readonly=False)

    # luar negeri
    almarhum_negara_tujuan_id = fields.Many2one(related="jenazah_id.negara_tujuan_id", readonly=False)

    # Document
    almarhum_surat_kematian = fields.Binary(related="jenazah_id.surat_kematian", readonly=False)
    almarhum_surat_kematian_filename = fields.Char(related="jenazah_id.surat_kematian_filename", readonly=False)
    almarhum_kartu_keluarga = fields.Binary(related='jenazah_id.kartu_keluarga', readonly=False)
    almarhum_kartu_keluarga_filename = fields.Char(related='jenazah_id.kartu_keluarga_filename', readonly=False)
    almarhum_surat_keterangan_kremasi = fields.Binary(related='jenazah_id.surat_keterangan_kremasi', readonly=False)
    almarhum_surat_keterangan_kremasi_filename = fields.Char(related='jenazah_id.surat_keterangan_kremasi_filename', readonly=False)
    almarhum_rekam_medis = fields.Binary(related='jenazah_id.rekam_medis', readonly=False)
    almarhum_rekam_medis_filename = fields.Char(related='jenazah_id.rekam_medis_filename', readonly=False)
    almarhum_izin_angkut = fields.Binary(related='jenazah_id.izin_angkut', readonly=False)
    almarhum_izin_angkut_filename = fields.Char(related='jenazah_id.izin_angkut_filename', readonly=False)
    almarhum_sertifikat_formalin = fields.Binary(related='jenazah_id.sertifikat_formalin', readonly=False)
    almarhum_sertifikat_formalin_filename = fields.Char(related='jenazah_id.sertifikat_formalin_filename', readonly=False)
    almarhum_izin_tahan_jenazah = fields.Binary(related='jenazah_id.izin_tahan_jenazah', readonly=False)
    almarhum_izin_tahan_jenazah_filename = fields.Char(related='jenazah_id.izin_tahan_jenazah_filename', readonly=False)
    almarhum_surat_berita_acara_kremasi = fields.Binary(related='jenazah_id.surat_berita_acara_kremasi', readonly=False)
    almarhum_surat_berita_acara_kremasi_filename = fields.Char(related='jenazah_id.surat_berita_acara_kremasi_filename', readonly=False)
    almarhum_surat_permohonan_pengawetan_jenazah = fields.Binary(related='jenazah_id.surat_permohonan_pengawetan_jenazah', readonly=False)
    almarhum_surat_permohonan_pengawetan_jenazah_filename = fields.Char(related='jenazah_id.surat_permohonan_pengawetan_jenazah_filename', readonly=False)
    almarhum_ktp_almarhum = fields.Binary(related='jenazah_id.ktp_almarhum', readonly=False)
    almarhum_ktp_almarhum_filename = fields.Char(related='jenazah_id.ktp_almarhum_filename', readonly=False)
    almarhum_ktp_penanggungjawab = fields.Binary(related='jenazah_id.ktp_penanggungjawab', readonly=False)
    almarhum_ktp_penanggungjawab_filename = fields.Char(related='jenazah_id.ktp_penanggungjawab_filename', readonly=False)
    almarhum_ktp_pemberi_kuasa = fields.Binary(related='jenazah_id.ktp_pemberi_kuasa', readonly=False)
    almarhum_ktp_pemberi_kuasa_filename = fields.Char(related='jenazah_id.ktp_pemberi_kuasa_filename', readonly=False)


    # informasi tambahan
    almarhum_penyakit = fields.Char(related="jenazah_id.penyakit", readonly=False)
    almarhum_tanggal_kedatangan = fields.Datetime(related="jenazah_id.tanggal_kedatangan", default=datetime.now(), readonly=False)
    almarhum_asal = fields.Char(related="jenazah_id.asal", readonly=False)
    almarhum_pelayanan = fields.Char(related="jenazah_id.pelayanan", readonly=False)
    almarhum_no_pol_kendaraan = fields.Char(related="jenazah_id.no_pol_kendaraan", readonly=False)
    almarhum_ruangan_id = fields.Many2one(related="jenazah_id.ruangan_id", readonly=False)
    almarhum_paket_id = fields.Many2one(related="jenazah_id.paket_id", readonly=False)
    almarhum_peti_id = fields.Many2one(related="jenazah_id.peti_id", readonly=False)
    # almarhum_is_transit = fields.Boolean(related="jenazah_id.is_transit", readonly=False)
    almarhum_tanggal_terima_abu = fields.Datetime(related="jenazah_id.tanggal_terima_abu", readonly=False)
    almarhum_jadwal_ibadah = fields.Datetime(related="jenazah_id.jadwal_ibadah", readonly=False)
    almarhum_nama_pemuka_agama = fields.Char(related="jenazah_id.nama_pemuka_agama", readonly=False)
    almarhum_paroki = fields.Char(related="jenazah_id.paroki", readonly=False)
    almarhum_tanggal_keberangkatan = fields.Datetime(related="jenazah_id.tanggal_keberangkatan", readonly=False)
    almarhum_keterangan = fields.Text(related="jenazah_id.keterangan", readonly=False)


    # report acara
    tujuan_string = fields.Char(compute='_compute_tujuan_string', string='Tujuan Lengkap')
    
    # report columbarium
    kegiatan_string = fields.Char(compute='_compute_tujuan_string', string='Kegiatan String')
    hari_string = fields.Char(compute='_compute_tujuan_string', string='Hari dan Tanggal')
    waktu_pelaksanaan_string = fields.Char(compute='_compute_tujuan_string', string='Waktu Pelaksanaan')

    

    @api.depends('jenazah_id','almarhum_tujuan','almarhum_jadwal_kremasi','almarhum_tanggal_pemakaman','almarhum_tujuan_pemakaman')
    def _compute_tujuan_string(self):
        for record in self:
            tujuan_string = ""
            
            kegiatan_string = ""
            hari_string = ""
            waktu_pelaksanaan_string = ""
            if record.almarhum_tujuan == 'kremasi' and record.almarhum_tujuan_kremasi != 'pemakaman':
                tujuan_string += "Krematorium Rumah Duka Carolus. "
                # tujuan_string += (record.almarhum_jadwal_kremasi+timedelta(hours=7)).strftime("%A, %d %b %Y %H:%M:%d") if record.almarhum_jadwal_kremasi else ""
                kegiatan_string = tujuan_string

                tujuan_string += format_datetime(record.almarhum_jadwal_kremasi+timedelta(hours=7), format="EEEE, dd MMM yyy 'pkl' H:mm 'WIB'", locale='id_ID') if record.almarhum_jadwal_kremasi else ""
                
                hari_string = format_datetime(record.almarhum_jadwal_kremasi+timedelta(hours=7), format="EEEE, dd MMM yyy", locale='id_ID') if record.almarhum_jadwal_kremasi else ""
                waktu_pelaksanaan_string = format_datetime(record.almarhum_jadwal_kremasi+timedelta(hours=7), format="'Pukul' H:mm 'WIB'", locale='id_ID') if record.almarhum_jadwal_kremasi else ""


            elif record.almarhum_tujuan == 'pemakaman' or record.almarhum_tujuan_kremasi == 'pemakaman':
                tujuan_string += "Pemakaman "
                tujuan_pemakaman = dict(self.jenazah_id._fields['tujuan_pemakaman'].selection).get(record.almarhum_tujuan_pemakaman) if record.almarhum_tujuan_pemakaman and dict(self.jenazah_id._fields['tujuan_pemakaman'].selection).get(record.almarhum_tujuan_pemakaman) else ""
                nama_pemakaman = ""
                if record.almarhum_tujuan_pemakaman:
                    if record.almarhum_tujuan_pemakaman == 'jabodetabek':
                        nama_pemakaman = ": "+ str(record.almarhum_jabodetabek_pemakaman_id.name) if record.almarhum_jabodetabek_pemakaman_id else ""
                    else:
                        nama_pemakaman = ": "+ str(record.almarhum_luar_jabodetabek_pemakaman_id.name) if record.almarhum_luar_jabodetabek_pemakaman_id else ""
                tujuan_string += "(%s %s)" % (tujuan_pemakaman,nama_pemakaman)

                kegiatan_string = tujuan_string

                tujuan_string += ". "+format_datetime(record.almarhum_tanggal_pemakaman+timedelta(hours=7), format="EEEE, dd MMM yyy 'pkl' H:mm 'WIB'", locale='id_ID') if record.almarhum_tanggal_pemakaman else ""
                hari_string = format_datetime(record.almarhum_tanggal_pemakaman+timedelta(hours=7), format="EEEE, dd MMM yyy", locale='id_ID') if record.almarhum_tanggal_pemakaman else ""
                waktu_pelaksanaan_string = format_datetime(record.almarhum_tanggal_pemakaman+timedelta(hours=7), format="'Pukul' H:mm 'WIB'", locale='id_ID') if record.almarhum_tanggal_pemakaman else ""

            elif record.almarhum_tujuan in ['columbarium','rumah']:
                tujuan_string += dict(self.jenazah_id._fields['tujuan'].selection).get(record.almarhum_tujuan) if record.almarhum_tujuan and dict(self.jenazah_id._fields['tujuan'].selection).get(record.almarhum_tujuan) else ""

                kegiatan_string = tujuan_string


            record.tujuan_string = tujuan_string

            record.kegiatan_string = kegiatan_string
            record.hari_string = hari_string
            record.waktu_pelaksanaan_string = waktu_pelaksanaan_string


    # def _get_columbarium_domain(self):
    #     categ_categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
    #     if categ_categ_columbarium:
    #         return "[('categ_id','=',{categ_categ_columbarium}),('qty_available','>=',1)]".format(
    #             categ_categ_columbarium = categ_categ_columbarium.id
    #         )
    #     return False

    # columbarium_id = fields.Many2one('product.product', string='Columbarium', domain=_get_columbarium_domain)
    # show_columbarium_id = fields.Boolean(compute='_compute_show_columbarium_id', string='Show columbarium')
    
    # @api.depends('almarhum_tujuan','almarhum_tujuan_kremasi')
    # def _compute_show_columbarium_id(self):
    #     for record in self:
    #         record.show_columbarium_id = False
    #         if record.almarhum_tujuan == 'columbarium' or (record.almarhum_tujuan == 'kremasi' and record.almarhum_tujuan_kremasi in ['disimpan','simpan_larung']):
    #             record.show_columbarium_id = True

    # DOCUMENT
    file_attachments = fields.Many2many(
        comodel_name="ir.attachment", 
        relation="msk_m2m_ir_attachment_relation",
        column1="m2m_id", 
        column2="attachment_id", 
        string="Attach File")


    @api.constrains('token')
    def _constrains_token(self):
        for record in self:
            if self.env[record._name].search_count([('id','!=',record.id),('token','=',record.token),('status','=','belum_diisi')]) >=1 :
                raise UserError("Make sure the token is unique and not used")

    @api.onchange('almarhum_tujuan')
    def _onchange_almarhum_tujuan(self):
        for record in self:
            if record.almarhum_tujuan != 'kremasi':
                record.almarhum_tujuan_kremasi = None
                record.almarhum_jadwal_kremasi = None
                record.almarhum_jadwal_transportasi = None
                record.almarhum_tujuan_larung = None
                record.almarhum_tujuan_simpan = None
                record.almarhum_transportasi_id = None
                record.almarhum_tujuan_pemakaman = None
                record.almarhum_jabodetabek_pemakaman_id = None
                record.almarhum_luar_jabodetabek_pemakaman_id = None
                # record.columbarium_id = None
            elif record.almarhum_tujuan != 'pemakaman':
                record.almarhum_jenis_transportasi = None
                record.almarhum_transportasi_id = None
                record.almarhum_transportasi = None
                record.almarhum_tanggal_pemakaman = None
                record.almarhum_tujuan_pemakaman = None
                record.almarhum_jabodetabek_pemakaman_id = None
            elif record.almarhum_tujuan != 'columbarium':
                record.almarhum_type_columbarium = None
                record.almarhum_asal_abu = None
                # record.columbarium_id = None

    @api.onchange('almarhum_tujuan_pemakaman')
    def _onchange_almarhum_tujuan_pemakaman(self):
        for record in self:
            if record.almarhum_tujuan_pemakaman == 'jabodetabek':
                record.almarhum_luar_jabodetabek_pemakaman_id = False
            elif record.almarhum_tujuan_pemakaman == 'luar jabodetabek':
                record.almarhum_jabodetabek_pemakaman_id = False
    
    ###############################################################
    ##   INHERITED METHOD
    ###############################################################
    @api.model
    def create(self, values):
        self.clear_caches()
        values['name'] = self.env['ir.sequence'].get_sequence(self._name,'RDC/CUST-FORM')

        if not values.get('jenazah_id') and values.get('almarhum_name'):
            jenazah_id = self.env['res.partner'].create({
                'is_jenazah': True,
                'name' : values.get('almarhum_name') if values.get('almarhum_name') else None,
            })
            values['jenazah_id'] = jenazah_id.id

            if not values.get('customer_id') and values.get('penanggungjawab_name'):
                customer_id = self.env['res.partner'].create({
                    'parent_id': jenazah_id.id if jenazah_id else None,
                    'name': values.get('penanggungjawab_name') if values.get('penanggungjawab_name') else None,
                    'is_penanggungjawab':True,
                    'is_customer': True,
                })
                values['customer_id'] = customer_id.id
            elif values.get('customer_id'):
                partner = self.env['res.partner'].browse(values.get('customer_id'))
                if partner:
                    partner.parent_id = jenazah_id.id if jenazah_id else None

            if values.get('almarhum_tujuan') == 'columbarium' and values.get('penanggungjawab2_name'):
                customer2_id = self.env['res.partner'].create({
                    'parent_id': jenazah_id.id if jenazah_id else None,
                    'name': values.get('penanggungjawab2_name') if values.get('penanggungjawab2_name') else None,
                    'is_penanggungjawab':True,
                    'is_customer': True,
                })
                values['customer2_id'] = customer2_id.id
            
            if values.get('customer2_id'):
                partner2 = self.env['res.partner'].browse(values.get('customer_id'))
                if partner2:
                    partner2.parent_id = jenazah_id.id if jenazah_id else None
                    
        res = super(CustomerFormWebsite,self).create(values)
        res.token = res.generate_unique_token()
        return res
    
    def write(self, values):
        for record in self:
            if not record.jenazah_id and values.get('almarhum_name'):
                record.jenazah_id = self.env['res.partner'].create({
                    'is_jenazah': True,
                    'name' : values.get('almarhum_name') if values.get('almarhum_name') else None,
                })
                if not record.customer_id and values.get('penanggungjawab_name'):
                    record.customer_id = self.env['res.partner'].create({
                        'parent_id': record.jenazah_id.id if record.jenazah_id else None,
                        'name': values.get('penanggungjawab_name') if values.get('penanggungjawab_name') else None,
                        'is_penanggungjawab':True,
                        'is_customer': True,
                    })
                elif record.customer_id:
                    record.customer_id.parent_id = record.jenazah_id.id if record.jenazah_id and record.customer_id.parent_id.id != record.jenazah_id.id else None
            
            if record.almarhum_tujuan == 'columbarium' and values.get('penanggungjawab2_name') and record.jenazah_id:
                record.customer2_id = self.env['res.partner'].create({
                    'parent_id': record.jenazah_id.id if record.jenazah_id else None,
                    'name': values.get('penanggungjawab2_name') if values.get('penanggungjawab2_name') else None,
                    'is_penanggungjawab':True,
                    'is_customer': True,
                })
            
            if record.customer2_id:
                    record.customer2_id.parent_id = record.jenazah_id.id if record.jenazah_id and record.customer2_id.parent_id.id != record.jenazah_id.id else None

        res = super(CustomerFormWebsite, self).write(values)
        return res

    ###############################################################
    ##   METHOD
    ###############################################################

    def generate_unique_token(self):
        unique_token_found = False
        while not unique_token_found:
            token = secrets.token_urlsafe(20)
            if not self.env[self._name].search_count([('token','=',token)]) >= 1:
                unique_token_found = True
        return token


    # def get_order_line_columbarium(self):
    #     for record in self:
    #         if record.columbarium_id:
    #             return [(0,0,{
    #                 'product_id': record.columbarium_id.id,
    #                 'name': 'RENTAL - {product_name}\n{pickup_date} to {return_date}'.format(
    #                     product_name = record.columbarium_id.name,
    #                     pickup_date = product_rent.pickup_date.strftime("%d/%m/%Y %H:%M:%S"),
    #                     return_date = product_rent.return_date.strftime("%d/%m/%Y %H:%M:%S"),
    #                 ),
    #                 'product_uom_qty': 1, #kalikan qty di dalam 1 bundle dan total paket yang dipilih
    #                 'price_unit': 0,
    #                 'tax_id': None,
    #                 'is_rental': True,
    #                 'reservation_begin': product_rent.pickup_date,
    #                 'pickup_date': product_rent.pickup_date,
    #                 'return_date': product_rent.return_date,
    #                 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.columbarium_id else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
    #             })]
    
    def action_add_vendor_larung(self):
        for record in self:
            if not record.sale_order_id:
                so_id = self.env['sale.order'].sudo().create({
                    'customer_form_id': record.id,
                    'partner_id': record.jenazah_id.id,
                    'penanggungjawab_id': record.customer_id.id if record.customer_id else None,
                    'penanggungjawab2_id': record.customer2_id.id if record.customer2_id else None,
                    'tanggal_keluar': record.jenazah_id.tanggal_keluar,
                    # 'order_line': order_line,
                })
            else:
                so_id = record.sale_order_id

            result = {
                'name': _('Choose Vendor'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('custom_sale_order.add_larung_wizard_view_form').id, 
                'res_model': 'add.larung.wizard', 
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_sale_order_id':so_id.id,
                    'default_name': "Pelarungan dengan tujuan ke {tujuan_larung}".format(
                        tujuan_larung = record.jenazah_id.tujuan_larung
                    )
                }
            }
            return result 

    def action_add_transportasi(self):
        for record in self:
            if not record.sale_order_id:
                so_id = self.env['sale.order'].sudo().create({
                    'customer_form_id': record.id,
                    'partner_id': record.jenazah_id.id,
                    'penanggungjawab_id': record.customer_id.id if record.customer_id else None,
                    'penanggungjawab2_id': record.customer2_id.id if record.customer2_id else None,
                    'tanggal_keluar': record.jenazah_id.tanggal_keluar,
                    # 'order_line': order_line,
                })
            else:
                so_id = record.sale_order_id

            result = {
                'type': 'ir.actions.act_window',
                'name': _('Tambah Transportasi Jenazah'),
                'res_model': 'add.transportasi.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.add_transportasi_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_sale_order_id':so_id.id,
                }
            }
            return result

    def action_create_so(self):
        for record in self:
            # order_line = record.get_order_line_columbarium() if record.columbarium_id else None
            result = {
                'name': _('Sale Order'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('sale_renting.rental_order_primary_form_view').id, 
                'res_model': 'sale.order', 
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {
                    'default_customer_form_id': record.id,
                    'default_partner_id': record.jenazah_id.id,
                    'default_penanggungjawab_id': record.customer_id.id if record.customer_id else None,
                    'default_penanggungjawab2_id': record.customer2_id.id if record.customer2_id else None,
                    'default_tanggal_keluar': record.jenazah_id.tanggal_keluar,
                    # 'default_order_line': order_line,
                }
            }
            return result  
        
    def action_create_so_with_pack(self):
        for record in self:
            # order_line = record.get_order_line_columbarium() if record.columbarium_id else None
            if not record.sale_order_id:
                so_id = self.env['sale.order'].sudo().create({
                    'customer_form_id': record.id,
                    'partner_id': record.jenazah_id.id,
                    'penanggungjawab_id': record.customer_id.id if record.customer_id else None,
                    'penanggungjawab2_id': record.customer2_id.id if record.customer2_id else None,
                    'tanggal_keluar': record.jenazah_id.tanggal_keluar,
                    # 'order_line': order_line,
                })
            else:
                so_id = record.sale_order_id

            result =  {
                'type': 'ir.actions.act_window',
                'name': _('Product Pack'),
                'res_model': 'bundle.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.ni_bundle_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'active_id': so_id.id,
                    'active_model':'sale.order',
                    'tanggal_kedatangan': record.almarhum_tanggal_kedatangan.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            return result  
    
    # tombol view sales order
    def action_view_so(self):
        for record in self:
            if record.sale_order_id:
                form_view_id = self.env.ref("sale.view_order_form").id
                name = 'Sale Order'
                if record.sale_order_id.is_rental_order:
                    form_view_id = self.env.ref("sale_renting.rental_order_primary_form_view").id
                    name = 'Rental Order'
        
                result = {
                    'name': _(name),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    # 'view_type': 'form',
                    'views': [(form_view_id, 'form')],
                    'res_id': self.sale_order_id.id,
                    'context': {'create': False},
                }
                return result  
            else:
                raise UserError("Sales Order not available")
    
    def _format_num_to_text(self, value):
        # value = self.num_to_text_id.round(value)
        value = int(value)
        # value = int(value) if int(value) == value else value
        return num2words(value, lang='id').title().lower()
        # return num2words(value, lang='en').title()

    
    def _translate(self, value, dest='id'):
        translator = Translator()
        translated = translator.translate(value, dest=dest)
        return translated.text
    
    def _delta_years(self, start_date, end_date):
        delta = relativedelta(end_date, start_date)
        return delta.years