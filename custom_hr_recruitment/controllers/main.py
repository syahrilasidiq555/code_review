# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
from werkzeug.exceptions import NotFound

import unicodedata
import base64
import json
from datetime import datetime

class WebsiteHrRecruitment(http.Controller):
    @http.route('''/jobs/apply/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("custom_hr_recruitment.apply_job", {
            'job': job,
            'error': error,
            'default': default,
        })
    

    # CUSTOMER FORM PAGE
    @http.route('/jobs/detail-form/<token>', type='http', auth="public", website=True, sitemap=True)
    def render_jobs_detail_form(self, token, **kwargs):
        applicant = request.env['hr.applicant'].sudo().search([('token','=',token),('is_second_form_filled','=',False)])
        
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("custom_hr_recruitment.apply_job_detail", {
            'applicant': applicant,
            'error': error,
            'default': default,
        })
    



    @http.route('/applicant/submit', type='http', auth="public", website=True)
    def applicant_submit(self, **kwargs):
        pendidikan_formal_ids = []
        pendidikan_nonformal_ids = []
        organization_ids = []
        anak_ids = []
        saudara_ids = []
        work_experience_ids = []
        foreign_language_ids = []
        local_language_ids = []
        skill_ids = []
        reference_ids = []


        # pendidikan_formal_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'pendidikan_formal_ids__nama_sekolah__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            pendidikan_formal_ids.append([0,0,{
                'pendidikan': kwargs.get(f'pendidikan_formal_ids__pendidikan__{line}',None),
                'nama_sekolah': kwargs.get(f'pendidikan_formal_ids__nama_sekolah__{line}',None),
                'jurusan': kwargs.get(f'pendidikan_formal_ids__jurusan__{line}',None),
                'tahun_mulai': int(kwargs.get(f'pendidikan_formal_ids__tahun_mulai__{line}')) if kwargs.get(f'pendidikan_formal_ids__tahun_mulai__{line}') else None,
                'tahun_akhir': int(kwargs.get(f'pendidikan_formal_ids__tahun_akhir__{line}')) if kwargs.get(f'pendidikan_formal_ids__tahun_akhir__{line}') else None,
                'ijazah': kwargs.get(f'pendidikan_formal_ids__ijazah__{line}',None),
                'ipk': float(kwargs.get(f'pendidikan_formal_ids__ipk__{line}')) if kwargs.get(f'pendidikan_formal_ids__ipk__{line}') else None,
                'kota': kwargs.get(f'pendidikan_formal_ids__kota__{line}',None),
            }])
        

        # pendidikan_nonformal_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'pendidikan_nonformal_ids__courses__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            pendidikan_nonformal_ids.append([0,0,{
                'courses': kwargs.get(f'pendidikan_nonformal_ids__courses__{line}', None),
                'lembaga_pendidikan': kwargs.get(f'pendidikan_nonformal_ids__lembaga_pendidikan__{line}', None),
                'tahun_mulai': int(kwargs.get(f'pendidikan_nonformal_ids__tahun_mulai__{line}')) if kwargs.get(f'pendidikan_nonformal_ids__tahun_mulai__{line}') else None,
                'tahun_akhir': int(kwargs.get(f'pendidikan_nonformal_ids__tahun_akhir__{line}')) if kwargs.get(f'pendidikan_nonformal_ids__tahun_akhir__{line}') else None,
                'ijazah': kwargs.get(f'pendidikan_nonformal_ids__ijazah__{line}', None),
                'tingkat': kwargs.get(f'pendidikan_nonformal_ids__tingkat__{line}', None),
                'kota': kwargs.get(f'pendidikan_nonformal_ids__kota__{line}', None),
            }])


        # organization_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'organization_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            organization_ids.append([0,0,{
                'name': kwargs.get(f'organization_ids__name__{line}',None),
                'jenis_kegiatan': kwargs.get(f'organization_ids__jenis_kegiatan__{line}',None),
                'position': kwargs.get(f'organization_ids__position__{line}',None),
                'tahun': int(kwargs.get(f'organization_ids__tahun__{line}')) if kwargs.get(f'organization_ids__tahun__{line}') else None,
            }])


        # anak_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'anak_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            anak_ids.append([0,0,{
                'name': kwargs.get(f'anak_ids__name__{line}',None),
                'tempat_lahir': kwargs.get(f'anak_ids__tempat_lahir__{line}',None),
                'tanggal_lahir': datetime.strptime(kwargs.get(f'anak_ids__tanggal_lahir__{line}'), '%d/%m/%Y') if kwargs.get(f'anak_ids__tanggal_lahir__{line}') else None,
                'jenis_kelamin': kwargs.get(f'anak_ids__jenis_kelamin__{line}',None),
                'no_handphone': kwargs.get(f'anak_ids__no_handphone__{line}',None),
                'pendidikan': kwargs.get(f'anak_ids__pendidikan__{line}',None),
                'pekerjaan': kwargs.get(f'anak_ids__pekerjaan__{line}',None),
            }])


        # saudara_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'saudara_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            saudara_ids.append([0,0,{
                'name': kwargs.get(f'saudara_ids__name__{line}',None),
                'tempat_lahir': kwargs.get(f'saudara_ids__tempat_lahir__{line}',None),
                'tanggal_lahir': datetime.strptime(kwargs.get(f'saudara_ids__tanggal_lahir__{line}'), '%d/%m/%Y') if kwargs.get(f'saudara_ids__tanggal_lahir__{line}') else None,
                'jenis_kelamin': kwargs.get(f'saudara_ids__jenis_kelamin__{line}',None),
                'no_handphone': kwargs.get(f'saudara_ids__no_handphone__{line}',None),
                'pendidikan': kwargs.get(f'saudara_ids__pendidikan__{line}',None),
                'pekerjaan': kwargs.get(f'saudara_ids__pekerjaan__{line}',None),
            }])

        
        # work_experience_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'work_experience_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            work_experience_ids.append([0,0,{
                'name': kwargs.get(f'work_experience_ids__name__{line}',None),
                'alamat': kwargs.get(f'work_experience_ids__alamat__{line}',None),
                'jobdesk': kwargs.get(f'work_experience_ids__jobdesk__{line}',None),
                'mulai': datetime.strptime(kwargs.get(f'work_experience_ids__mulai__{line}'), '%Y-%m-%d') if kwargs.get(f'work_experience_ids__mulai__{line}') else None,
                'selesai': datetime.strptime(kwargs.get(f'work_experience_ids__selesai__{line}'), '%Y-%m-%d') if kwargs.get(f'work_experience_ids__selesai__{line}') else None,
                'jabatan': kwargs.get(f'work_experience_ids__jabatan__{line}',None),
                'salary': float(kwargs.get(f'work_experience_ids__salary__{line}','0')),
                'alasan_keluar': kwargs.get(f'work_experience_ids__alasan_keluar__{line}',None),
            }])

        
        # foreign_language_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'foreign_language_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            foreign_language_ids.append([0,0,{
                'name': kwargs.get(f'foreign_language_ids__name__{line}', None),
                'tingkat': kwargs.get(f'foreign_language_ids__tingkat__{line}', None),
            }])

        # local_language_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'local_language_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            local_language_ids.append([0,0,{
                'name': kwargs.get(f'local_language_ids__name__{line}', None),
                'tingkat': kwargs.get(f'local_language_ids__tingkat__{line}', None),
            }])

        
        # skill_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'skill_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            skill_ids.append([0,0,{
                'name': kwargs.get(f'skill_ids__name__{line}',None),
                'tingkat': kwargs.get(f'skill_ids__tingkat__{line}',None),
            }])

        
        # reference_ids
        list_line = []
        rows = [key for key, value in kwargs.items() if 'reference_ids__name__' in key.lower()]
        for x in rows:
            arr = x.split('__')
            if arr[2]:
                list_line.append(arr[2])
        for line in list_line:
            reference_ids.append([0,0,{
                'name': kwargs.get(f'reference_ids__name__{line}', None),
                'nama_perusahaan': kwargs.get(f'reference_ids__nama_perusahaan__{line}', None),
                'jabatan': kwargs.get(f'reference_ids__jabatan__{line}', None),
                'alamat': kwargs.get(f'reference_ids__alamat__{line}', None),
            }])


        data = {
            'name': f"{kwargs.get('partner_name','')}'s Application",
            'job_id': int(kwargs.get('job_id')) if kwargs.get('job_id') else None,
            'department_id': int(kwargs.get('department_id')) if kwargs.get('department_id') else None,
            'partner_name' : kwargs.get('partner_name',None),
            'nama_panggilan' : kwargs.get('nama_panggilan',None),
            'jenis_kelamin' : kwargs.get('jenis_kelamin',None),
            'tempat_lahir' : kwargs.get('tempat_lahir',None),
            'tanggal_lahir' : datetime.strptime(kwargs.get('tanggal_lahir'), '%Y-%m-%d') if kwargs.get('tanggal_lahir') else None,
            'agama' : kwargs.get('agama',None),
            'no_ktp' : kwargs.get('no_ktp',None),
            'kewarganegaraan' : kwargs.get('kewarganegaraan',None),
            'alamat_tetap' : kwargs.get('alamat_tetap',None),
            'kota_tetap' : kwargs.get('kota_tetap',None),
            'kode_pos_tetap' : kwargs.get('kode_pos_tetap',None),
            'alamat_sekarang' : kwargs.get('alamat_sekarang',None),
            'kota_sekarang' : kwargs.get('kota_sekarang',None),
            'kode_pos_sekarang' : kwargs.get('kode_pos_sekarang',None),
            'partner_phone' : kwargs.get('partner_phone',None),
            'partner_mobile' : kwargs.get('partner_mobile',None),
            'email_from' : kwargs.get('email_from',None),
            'no_sim_a' : kwargs.get('no_sim_a',None),
            'no_sim_b1' : kwargs.get('no_sim_b1',None),
            'no_sim_b2' : kwargs.get('no_sim_b2',None),
            'no_sim_c' : kwargs.get('no_sim_c',None),
            'gol_darah' : kwargs.get('gol_darah',None),
            'berat_badan' : float(kwargs.get('berat_badan')) if kwargs.get('berat_badan') else None,
            'tinggi_badan' : float(kwargs.get('tinggi_badan')) if kwargs.get('tinggi_badan') else None,
            'status_pernikahan' : kwargs.get('status_pernikahan',None),

            'pendidikan_formal_ids':pendidikan_formal_ids,
            'pendidikan_nonformal_ids':pendidikan_nonformal_ids,
            'organization_ids':organization_ids,

            'pendidikan_terpuas': kwargs.get('pendidikan_terpuas',None),
            'pendidikan_tertidakpuas': kwargs.get('pendidikan_tertidakpuas',None),
            'pendidikan_pembiaya': kwargs.get('pendidikan_pembiaya',None),


            'ayah_nama_lengkap': kwargs.get('ayah_nama_lengkap',None),
            'ayah_tempat_lahir': kwargs.get('ayah_tempat_lahir',None),
            'ayah_tanggal_lahir': datetime.strptime(kwargs.get('ayah_tanggal_lahir'), '%d/%m/%Y') if kwargs.get('ayah_tanggal_lahir') else None,
            'ayah_no_handphone': kwargs.get('ayah_no_handphone',None),
            'ayah_alamat': kwargs.get('ayah_alamat',None),
            'ayah_pendidikan': kwargs.get('ayah_pendidikan',None),
            'ayah_pekerjaan': kwargs.get('ayah_pekerjaan',None),
            'ibu_nama_lengkap': kwargs.get('ibu_nama_lengkap',None),
            'ibu_tempat_lahir': kwargs.get('ibu_tempat_lahir',None),
            'ibu_tanggal_lahir': datetime.strptime(kwargs.get('ibu_tanggal_lahir'), '%d/%m/%Y') if kwargs.get('ibu_tanggal_lahir') else None,
            'ibu_no_handphone': kwargs.get('ibu_no_handphone',None),
            'ibu_alamat': kwargs.get('ibu_alamat',None),
            'ibu_pendidikan': kwargs.get('ibu_pendidikan',None),
            'ibu_pekerjaan': kwargs.get('ibu_pekerjaan',None),
            'jenis_pasangan': kwargs.get('jenis_pasangan',None),
            'pasangan_nama_lengkap': kwargs.get('pasangan_nama_lengkap',None),
            'pasangan_tempat_lahir': kwargs.get('pasangan_tempat_lahir',None),
            'pasangan_tanggal_lahir': datetime.strptime(kwargs.get('pasangan_tanggal_lahir'), '%d/%m/%Y') if kwargs.get('pasangan_tanggal_lahir') else None,
            'pasangan_no_handphone': kwargs.get('pasangan_no_handphone',None),
            'pasangan_alamat': kwargs.get('pasangan_alamat',None),
            'pasangan_pendidikan': kwargs.get('pasangan_pendidikan',None),
            'pasangan_pekerjaan': kwargs.get('pasangan_pekerjaan',None),
            'anak_ids': anak_ids,
            'saudara_ids': saudara_ids,
            'is_saudara_masih_dibantu': eval(kwargs.get('is_saudara_masih_dibantu')) if kwargs.get('is_saudara_masih_dibantu') else None,
            'saudara_bantuan_dari': kwargs.get('saudara_bantuan_dari',None),
            'jenis_bentuk_bantuan': kwargs.get('jenis_bentuk_bantuan',None),
            'is_tanggungan_lain': eval(kwargs.get('is_tanggungan_lain')) if kwargs.get('is_tanggungan_lain') else None,
            'tanggungan_lain': kwargs.get('tanggungan_lain',None),
            'is_meninggalkan_keluarga': eval(kwargs.get('is_meninggalkan_keluarga')) if kwargs.get('is_meninggalkan_keluarga') else None,
            'keperluan_meninggalkan_keluarga': kwargs.get('keperluan_meninggalkan_keluarga',None),
            'rumah_tinggal': kwargs.get('rumah_tinggal',None),
            

            'work_experience_ids':work_experience_ids,
            'jumlah_bawahan': int(kwargs.get('jumlah_bawahan')) if kwargs.get('jumlah_bawahan') else None,
            'is_buat_pembaharuan': eval(kwargs.get('is_buat_pembaharuan')) if kwargs.get('is_buat_pembaharuan') else None,
            'pembaharuan_dibuat': kwargs.get('pembaharuan_dibuat', None),

            'foreign_language_ids': foreign_language_ids,
            'local_language_ids': local_language_ids,

            'skill_ids': skill_ids,

            'mengapa_melamar': kwargs.get('mengapa_melamar',None),
            'yg_diketahui_dr_jabatan': kwargs.get('yg_diketahui_dr_jabatan',None),
            'is_dipindah_jabatan': kwargs.get('is_dipindah_jabatan',None),
            'alasan_pindah_jabatan': kwargs.get('alasan_pindah_jabatan',None),
            'lingkungan_disenangi': kwargs.get('lingkungan_disenangi',None),
            'alasan_lingkungan_tsb': kwargs.get('alasan_lingkungan_tsb',None),
            'cita2': kwargs.get('cita2',None),
            'kegemaran': kwargs.get('kegemaran',None),
            'kegiatan_luang': kwargs.get('kegiatan_luang',None),
            'kelebihan': kwargs.get('kelebihan',None),
            'kekurangan': kwargs.get('kekurangan',None),


            'pernah_sakit_keras': eval(kwargs.get('pernah_sakit_keras')) if kwargs.get('pernah_sakit_keras') else None,
            'sakit_keras_apa': kwargs.get('sakit_keras_apa', None),
            'kesehatan_keluarga_baik': eval(kwargs.get('kesehatan_keluarga_baik')) if kwargs.get('kesehatan_keluarga_baik') else None,
            'keluarga_sakit_apa': kwargs.get('keluarga_sakit_apa', None),
            'pernah_kecelakaan': eval(kwargs.get('pernah_kecelakaan')) if kwargs.get('pernah_kecelakaan') else None,
            'kecelakaan_apa': kwargs.get('kecelakaan_apa', None),

            'harapan_gaji': float(kwargs.get('harapan_gaji','0')),
            'harapan_fasilitas': kwargs.get('harapan_fasilitas',None),
            'kesiapan_bekerja': kwargs.get('kesiapan_bekerja',None),
            'bersedia_diluar_bdg': eval(kwargs.get('bersedia_diluar_bdg')) if kwargs.get('bersedia_diluar_bdg') else None,
            'alasan_tidak_diluar_bdg': kwargs.get('alasan_tidak_diluar_bdg',None),
            'alasan_bekerja_disini': kwargs.get('alasan_bekerja_disini',None),
            'sudah_pernah_melamar': eval(kwargs.get('sudah_pernah_melamar')) if kwargs.get('sudah_pernah_melamar') else None,
            'kapan_melamar': kwargs.get('kapan_melamar',None),
            'kendaraan': kwargs.get('kendaraan',None),
            'pernah_psikotest': eval(kwargs.get('pernah_psikotest')) if kwargs.get('pernah_psikotest') else None,
            'terakhir_psikotest': kwargs.get('terakhir_psikotest',None),

            'nama_kenalan1': kwargs.get('nama_kenalan1',None),
            'bagian_kenalan1': kwargs.get('bagian_kenalan1',None),
            'nama_kenalan2': kwargs.get('nama_kenalan2',None),
            'bagian_kenalan2': kwargs.get('bagian_kenalan2',None),
            'reference_ids': reference_ids,
        }
        
        if kwargs.get('token',''):
            applicant_id = request.env['hr.applicant'].sudo().search([('token','=',kwargs.get('token',''))])
            if applicant_id:
                applicant_id.sudo().write(data)
        else:
            applicant_id = request.env['hr.applicant'].sudo().create(data)
            
            files = []
            files.append(kwargs.get('cv'))        
            files.append(kwargs.get('ijazah'))        
            files.append(kwargs.get('ktp'))        
            files.append(kwargs.get('npwp'))     

            if files:
                for file in files:
                    filename = file.filename
                    if request.httprequest.user_agent.browser == 'safari':
                        filename = unicodedata.normalize('NFD', file.filename)
        
                    try:
                        attachment = request.env['ir.attachment'].sudo().create({
                            'name': filename,
                            'type': 'binary',
                            'datas': base64.b64encode(file.read()),
                            'res_model': 'hr.applicant',
                            'res_id': applicant_id.id
                        })
                    except Exception:
                        data['message'] = 'Cannot Upload Attachment!'
            

            # return json.dumps(data)
            # return request.render('custom_hr_recruitment.applicant_response', data)
        return request.redirect('/job-thank-you')