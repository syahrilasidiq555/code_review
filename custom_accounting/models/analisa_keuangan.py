from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

class AnalisaKeuangan(models.Model):
    _name = "analisa.keuangan"
    _description = "Analisa Keuangan"

    @api.model
    def get_period(self,period="month"):
        date_now = datetime.now()
        if period == 'week':
            start_date = date_now - timedelta(days=date_now.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = date_now.replace(day=1,hour=0,minute=0,second=0)
            next_month = date_now.replace(day=1) + relativedelta(days=31)
            end_date = next_month.replace(day=1, hour=23,minute=59,second=59) - relativedelta(days=1)
        elif period == 'year':
            start_date = date_now.replace(day=1,month=1,hour=0,minute=0,second=0)
            next_year = start_date + relativedelta(years=1)
            end_date = next_year.replace(hour=23,minute=59,second=59) - relativedelta(days=1)
        elif period == 'day':
            start_date = date_now.replace(hour=0,minute=0,second=0)
            end_date = start_date.replace(hour=23,minute=59,second=59)
        else:
            return False
        
        return {
            'start_date':start_date.strftime("%Y-%m-%d"),
            'end_date':end_date.strftime("%Y-%m-%d"),
        }
    
    @api.model
    def get_rasio_hutang(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.internal_group','in',['liability','asset']),
        ]

        data = self.env[model].sudo().search(domain)
        coa_hutang = data.filtered(lambda x: x.account_id.user_type_id.internal_group == 'liability').mapped('account_id') # liability
        coa_aktiva = data.filtered(lambda x: x.account_id.user_type_id.internal_group == 'asset').mapped('account_id') # asset

        value_hutang = sum(data.filtered(lambda x: x.account_id in coa_hutang.ids).mapped('balance'))
        value_aktiva = sum(data.filtered(lambda x: x.account_id in coa_aktiva.ids).mapped('balance'))

        # Rumus = hutang / aktiva * 100
        if value_aktiva != 0:
            rasio_hutang = (value_hutang / value_aktiva) * 100 
        else:
            rasio_hutang = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Hutang)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_hutang

    @api.model
    def get_rasio_hutang_pendekatan_modal(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'

        modal_selection = ['Ekuitas dan Modal','Aktiva Bersih Tidak Terikat']
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.internal_group','=','liability'),
            ('account_id.user_type_id.name','in',modal_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_hutang = data.filtered(lambda x: x.account_id.user_type_id.internal_group == 'liability').mapped('account_id') # liability
        coa_modal = data.filtered(lambda x: x.account_id.user_type_id.name in modal_selection).mapped('account_id') # 'Ekuitas dan Modal','Aktiva Bersih Tidak Terikat'

        value_hutang = sum(data.filtered(lambda x: x.account_id in coa_hutang.ids).mapped('balance'))
        value_modal = sum(data.filtered(lambda x: x.account_id in coa_modal.ids).mapped('balance'))

        # Rumus = hutang / modal * 100
        if value_modal != 0:
            rasio_hutang_pendekatan_modal = (value_hutang / value_modal) * 100 
        else:
            rasio_hutang_pendekatan_modal = 0
        
        if get_action:
            return {
                'name': _('Account Move Line (Rasio Hutang Pendekatan Modal)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_hutang_pendekatan_modal
    
    @api.model
    def get_rasio_lancar(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'

        aktiva_lancar_selection = [
            'Aset Lancar',
            'Kas dan Setara Kas',
            'Kas',
            'Bank',
            'Deposito Berjangka',
            'Piutang',
            'Uang Muka',
            'Persediaan',
            'Biaya Dibayar Dimuka',
            'Aset Lancar Lainnya'
        ]
        hutang_lancar_selection = [
            'Kewajiban',
            'Hutang Usaha',
            'Hutang Pajak',
            'Liabilitas Jangka Panjang',
            'Liabilitas',
            'Liabilitas Jangka Pendek',
            'Pendapatan Dibayar Dimuka'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',hutang_lancar_selection),
            ('account_id.user_type_id.name','in',aktiva_lancar_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_aktiva_lancar = data.filtered(lambda x: x.account_id.user_type_id.name in aktiva_lancar_selection).mapped('account_id') # aktiva lancar
        coa_hutang_lancar = data.filtered(lambda x: x.account_id.user_type_id.name in hutang_lancar_selection).mapped('account_id') # hutang lancar

        value_aktiva_lancar = sum(data.filtered(lambda x: x.account_id in coa_aktiva_lancar.ids).mapped('balance'))
        value_hutang_lancar = sum(data.filtered(lambda x: x.account_id in coa_hutang_lancar.ids).mapped('balance'))

        # Rumus = aktiva lancar / hutang lancar * 100
        if value_hutang_lancar != 0:
            rasio_lancar = (value_aktiva_lancar / value_hutang_lancar) * 100 
        else:
            rasio_lancar = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Lancar)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_lancar
    
    @api.model
    def get_rasio_kas(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        kas_setara_kas_selection = [
            'Kas dan Setara Kas',
            'Kas'

        ]
        hutang_lancar_selection = [
            'Kewajiban',
            'Hutang Usaha',
            'Hutang Pajak',
            'Liabilitas Jangka Panjang',
            'Liabilitas',
            'Liabilitas Jangka Pendek',
            'Pendapatan Dibayar Dimuka'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',hutang_lancar_selection),
            ('account_id.user_type_id.name','in',kas_setara_kas_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_kas_setara_kas = data.filtered(lambda x: x.account_id.user_type_id.name in kas_setara_kas_selection).mapped('account_id') # kas & setara kas
        coa_hutang_lancar = data.filtered(lambda x: x.account_id.user_type_id.name in hutang_lancar_selection).mapped('account_id') # hutang lancar

        value_kas_setara_kas = sum(data.filtered(lambda x: x.account_id in coa_kas_setara_kas.ids).mapped('balance'))
        value_hutang_lancar = sum(data.filtered(lambda x: x.account_id in coa_hutang_lancar.ids).mapped('balance'))

        # Rumus = ((kas + aktiva setara kas) / hutang lancar) * 100
        if value_hutang_lancar != 0:
            rasio_kas = (value_kas_setara_kas / value_hutang_lancar) * 100 
        else:
            rasio_kas = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Kas)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_kas
    
    @api.model
    def get_rasio_cepat(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        aktiva_lancar_selection = [
            'Aset Lancar',
            'Kas dan Setara Kas',
            'Kas',
            'Bank',
            'Deposito Berjangka',
            'Piutang',
            'Uang Muka',
            'Persediaan',
            'Biaya Dibayar Dimuka',
            'Aset Lancar Lainnya'
        ]
        hutang_lancar_selection = [
            'Kewajiban',
            'Hutang Usaha',
            'Hutang Pajak',
            'Liabilitas Jangka Panjang',
            'Liabilitas',
            'Liabilitas Jangka Pendek',
            'Pendapatan Dibayar Dimuka'
        ]
        persediaan_selection = [
            'Persediaan'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',hutang_lancar_selection),
            ('account_id.user_type_id.name','in',aktiva_lancar_selection),
            ('account_id.user_type_id.name','in',persediaan_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_aktiva_lancar = data.filtered(lambda x: x.account_id.user_type_id.name in aktiva_lancar_selection).mapped('account_id') # aktiva lancar
        coa_hutang_lancar = data.filtered(lambda x: x.account_id.user_type_id.name in hutang_lancar_selection).mapped('account_id') # hutang lancar
        coa_persediaan = data.filtered(lambda x: x.account_id.user_type_id.name in persediaan_selection).mapped('account_id') # persediaan

        value_aktiva_lancar = sum(data.filtered(lambda x: x.account_id in coa_aktiva_lancar.ids).mapped('balance'))
        value_hutang_lancar = sum(data.filtered(lambda x: x.account_id in coa_hutang_lancar.ids).mapped('balance'))
        value_persediaan = sum(data.filtered(lambda x: x.account_id in coa_persediaan.ids).mapped('balance'))

        # Rumus = ((aktiva lancar - persediaan) / hutang lancar) * 100
        if value_hutang_lancar != 0:
            rasio_cepat = ((value_aktiva_lancar - value_persediaan) / value_hutang_lancar) * 100 
        else:
            rasio_cepat = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Cepat)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_cepat
    
    @api.model
    def get_rasio_perputaran_persediaan(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        hpp_selection = [
            'Harga Pokok Pendapatan'
        ]
        persediaan_selection = [
            'Persediaan'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',hpp_selection),
            ('account_id.user_type_id.name','in',persediaan_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_hpp = data.filtered(lambda x: x.account_id.user_type_id.name in hpp_selection).mapped('account_id') # hpp
        coa_persediaan = data.filtered(lambda x: x.account_id.user_type_id.name in persediaan_selection).mapped('account_id') # persediaan

        value_hpp = sum(data.filtered(lambda x: x.account_id in coa_hpp.ids).mapped('balance'))
        value_persediaan = sum(data.filtered(lambda x: x.account_id in coa_persediaan.ids).mapped('balance'))

        # Rumus = hpp / persediaan * 100
        if value_persediaan != 0:
            rasio_perputaran_persediaan = (value_hpp / value_persediaan) * 100 
        else:
            rasio_perputaran_persediaan = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Perputaran Persediaan)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_perputaran_persediaan

    @api.model
    def get_rasio_perputaran_piutang(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        piutang_selection = [
            'Piutang'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',piutang_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_piutang = data.filtered(lambda x: x.account_id.user_type_id.name in piutang_selection).mapped('account_id') # piutang

        value_piutang = sum(data.filtered(lambda x: x.account_id in coa_piutang.ids).mapped('balance'))
        value_avg_piutang = value_piutang / len(data.filtered(lambda x: x.account_id in coa_piutang.ids).mapped('balance')) if value_piutang != 0 else 0

        # Rumus = piutang / avg piutang * 100
        if value_avg_piutang != 0:
            rasio_perputaran_piutang = (value_piutang / value_avg_piutang) * 100 
        else:
            rasio_perputaran_piutang = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Perputaran Piutang)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_perputaran_piutang

    @api.model
    def get_rasio_perputaran_aktiva_tetap(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        aktiva_tetap_selection = [
            'Aset Lancar',
            'Kas dan Setara Kas',
            'Kas',
            'Bank',
            'Deposito Berjangka',
            'Piutang',
            'Uang Muka',
            'Persediaan',
            'Biaya Dibayar Dimuka',
            'Aset Lancar Lainnya'
        ]
        penjualan_selection = [
            'Pendapatan',
            'Pendapatan Peti',
            'Pendapatan Ruang Semayam',
            'Pendapatan Perawatan Jenasah',
            'Pendapatan Transportasi',
            'Pendapatan Kremasi',
            'Pendapatan Parkir',
            'Pendapatan Lainnya'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',aktiva_tetap_selection),
            ('account_id.user_type_id.name','in',penjualan_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_aktiva_tetap = data.filtered(lambda x: x.account_id.user_type_id.name in aktiva_tetap_selection).mapped('account_id') # aktiva tetap
        coa_penjualan = data.filtered(lambda x: x.account_id.user_type_id.name in penjualan_selection).mapped('account_id') # penjualan

        value_aktiva_tetap = sum(data.filtered(lambda x: x.account_id in coa_aktiva_tetap.ids).mapped('balance'))
        value_penjualan = sum(data.filtered(lambda x: x.account_id in coa_penjualan.ids).mapped('balance'))

        # Rumus = penjualan / aktiva tetap * 100
        if value_aktiva_tetap != 0:
            rasio_perputaran_aktiva_tetap = (value_penjualan / value_aktiva_tetap) * 100 
        else:
            rasio_perputaran_aktiva_tetap = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Perputaran Aktiva Tetap)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_perputaran_aktiva_tetap

    @api.model
    def get_rasio_perputaran_total_aktiva(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        
        aktiva_selection = [
            'Aset Lancar',
            'Kas dan Setara Kas',
            'Kas',
            'Bank',
            'Deposito Berjangka',
            'Piutang',
            'Uang Muka',
            'Persediaan',
            'Biaya Dibayar Dimuka',
            'Aset Lancar Lainnya'
        ]
        penjualan_selection = [
            'Pendapatan',
            'Pendapatan Peti',
            'Pendapatan Ruang Semayam',
            'Pendapatan Perawatan Jenasah',
            'Pendapatan Transportasi',
            'Pendapatan Kremasi',
            'Pendapatan Parkir',
            'Pendapatan Lainnya'
        ]

        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
            ('account_id.user_type_id.name','in',aktiva_selection),
            ('account_id.user_type_id.name','in',penjualan_selection),
        ]

        data = self.env[model].sudo().search(domain)
        coa_aktiva = data.filtered(lambda x: x.account_id.user_type_id.name in aktiva_selection).mapped('account_id') # aktiva
        coa_penjualan = data.filtered(lambda x: x.account_id.user_type_id.name in penjualan_selection).mapped('account_id') # penjualan

        value_aktiva = sum(data.filtered(lambda x: x.account_id in coa_aktiva.ids).mapped('balance'))
        value_penjualan = sum(data.filtered(lambda x: x.account_id in coa_penjualan.ids).mapped('balance'))

        # Rumus = penjualan / aktiva tetap * 100
        if value_aktiva != 0:
            rasio_perputaran_total_aktiva = (value_penjualan / value_aktiva) * 100 
        else:
            rasio_perputaran_total_aktiva = 0

        if get_action:
            return {
                'name': _('Account Move Line (Rasio Perputaran Total Aktiva)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_perputaran_total_aktiva
    
    @api.model
    def get_rasio_margin_laba_kotor(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
        ]
        rasio_margin_laba_kotor = 0 #self.env[model].sudo().search_count(domain)
        if get_action:
            return {
                'name': _('Account Move Line (Rasio Margin Laba Kotor)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_margin_laba_kotor
    
    @api.model
    def get_rasio_margin_laba_bersih(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
        ]
        rasio_margin_laba_bersih = 0 #self.env[model].sudo().search_count(domain)
        if get_action:
            return {
                'name': _('Account Move Line (Rasio Margin Laba Bersih)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_margin_laba_bersih
    
    @api.model
    def get_rasio_margin_laba_operasi(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
        ]
        rasio_margin_laba_operasi = 0 #self.env[model].sudo().search_count(domain)
        if get_action:
            return {
                'name': _('Account Move Line (Rasio Margin Laba Operasi)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return rasio_margin_laba_operasi
    
    @api.model
    def get_return_on_investment(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
        ]
        return_on_investment = 0 #self.env[model].sudo().search_count(domain)
        if get_action:
            return {
                'name': _('Account Move Line (Return On Investment)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return return_on_investment
    
    @api.model
    def get_return_on_assets(self, period="month", get_action=False):
        date_period = self.get_period(period=period)
        model = 'account.move.line'
        domain = [
            ('move_id.state','=','posted'),
            ('date','>=',date_period['start_date']),
            ('date','<=',date_period['end_date']),
        ]
        return_on_assets = 0 #self.env[model].sudo().search_count(domain)
        if get_action:
            return {
                'name': _('Account Move Line (Return On Assets)'),
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'tree,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': domain,
                'context': {'create':False, 'edit':False, 'delete':False},
                'target': 'current',
            }

        return return_on_assets

    @api.model
    def get_dashboard_value(self, period="month"):
        companies = self.env['res.company'].sudo().search([
            ('id','in',self.env.context['allowed_company_ids'])
        ])
        
        company_names = "("
        for company in companies:
            company_names += str(company.name) + ', '
        company_names = company_names[:-2] + str(')')

        # get total pasien
        rasio_hutang = self.get_rasio_hutang(period=period)
        rasio_hutang_pendekatan_modal = self.get_rasio_hutang_pendekatan_modal(period=period)
        rasio_lancar = self.get_rasio_lancar(period=period)
        rasio_kas = self.get_rasio_kas(period=period)
        rasio_cepat = self.get_rasio_cepat(period=period)
        rasio_perputaran_persediaan = self.get_rasio_perputaran_persediaan(period=period)
        rasio_perputaran_piutang = self.get_rasio_perputaran_piutang(period=period)
        rasio_perputaran_aktiva_tetap = self.get_rasio_perputaran_aktiva_tetap(period=period)
        rasio_perputaran_total_aktiva = self.get_rasio_perputaran_total_aktiva(period=period)
        rasio_margin_laba_kotor = self.get_rasio_margin_laba_kotor(period=period)
        rasio_margin_laba_bersih = self.get_rasio_margin_laba_bersih(period=period)
        rasio_margin_laba_operasi = self.get_rasio_margin_laba_operasi(period=period)
        return_on_investment = self.get_return_on_investment(period=period)
        return_on_assets = self.get_return_on_assets(period=period)

        return {
            'company_names': company_names,
            'rasio_hutang':rasio_hutang,
            'rasio_hutang_pendekatan_modal':rasio_hutang_pendekatan_modal,
            'rasio_lancar':rasio_lancar,
            'rasio_kas':rasio_kas,
            'rasio_cepat':rasio_cepat,
            'rasio_perputaran_persediaan':rasio_perputaran_persediaan,
            'rasio_perputaran_piutang':rasio_perputaran_piutang,
            'rasio_perputaran_aktiva_tetap':rasio_perputaran_aktiva_tetap,
            'rasio_perputaran_total_aktiva':rasio_perputaran_total_aktiva,
            'rasio_margin_laba_kotor':rasio_margin_laba_kotor,
            'rasio_margin_laba_bersih':rasio_margin_laba_bersih,
            'rasio_margin_laba_operasi':rasio_margin_laba_operasi,
            'return_on_investment':return_on_investment,
            'return_on_assets':return_on_assets,
        }