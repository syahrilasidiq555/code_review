from odoo import models, exceptions, _, osv
import time
import logging 
from odoo.exceptions import MissingError
from datetime import datetime,timedelta

class report_performance_atasan1_done_xls(models.AbstractModel):
	_name = 'report.dym_performance_appraisal.report_atasan1_done_xls'
	_inherit = 'report.report_xlsx.abstract'


	def generate_xlsx_report(self, workbook, data, lines):
		_logger = logging.getLogger(__name__)
		department_ids = data.get('department_ids')
		start_date = data.get('start_date')
		end_date = data.get('end_date')
		tipe_report = data.get('tipe_report')
		periode = data.get('periode')

		where_department = ""
		where_start_date = ""
		where_end_date = ""
		nama_sheet = ""
		where_periode = ""

		if tipe_report == 'form_a':
			nama_sheet = "Report PK Form A"
			if department_ids:
				where_department = " and dep.id in %s"% str(tuple(department_ids)).replace(',)', ')')
			if start_date:
				where_start_date = " and a.date >= '%s'"% str(start_date)
			if end_date:
				where_end_date = " and a.date <= '%s'"% str(end_date)
			if periode:
				where_periode = " and a.periode = '%s'"% str(periode)
			query="""
				select he.name as karyawan,he.barcode as nik,dep.loc as cabang,dep.name as department_name,
				case when a.state = 'draft' then 'Draft'
					when a.state = 'start' then 'Start'
					when a.state = 'employee_answer' then 'Employee Answered'
					when a.state = 'atasan1_answer' then 'Atasan 1 Answered'
					when a.state = 'atasan2_answer' then 'Atasan 2 Answered'
					when a.state = 'posted' then 'Posted'
					when a.state = 'cancel' then 'Cancel' end as state,
				a.kualitas as kualitas_employee,
				a.kuantitas as kuantitas_employee,
				a.kerjasama as kerjasama_employee,
				a.disiplin as disiplin_employee,
				a.kompetensi as kompetensi_employee,
				a.kreatifitas as kreatifitas_employee,
				a.konsistensi as konsistensi_employee,

				he_1.name as atasan_1,
				a.kualitas_1 as kualitas_atasan1,
				a.kuantitas_1 as kuantitas_atasan1,
				a.kerjasama_1 as kerjasama_atasan1,
				a.disiplin_1 as disiplin_atasan1,
				a.kompetensi_1 as kompetensi_atasan1,
				a.kreatifitas_1 as kreatifitas_atasan1,
				a.konsistensi_1 as konsistensi_atasan1,

				he_2.name as atasan_2,
				a.kualitas_2 as kualitas_atasan2,
				a.kuantitas_2 as kuantitas_atasan2,
				a.kerjasama_2 as kerjasama_atasan2,
				a.disiplin_2 as disiplin_atasan2,
				a.kompetensi_2 as kompetensi_atasan2,
				a.kreatifitas_2 as kreatifitas_atasan2,
				a.konsistensi_2 as konsistensi_atasan2,

				a.kualitas_2::integer * 20 as score_kualitas,
				a.kuantitas_2::integer * 20 as score_kuantitas,
				a.kerjasama_2::integer * 15 as score_kerjasama,
				a.disiplin_2::integer * 15 as score_disiplin,
				a.kompetensi_2::integer * 10 as score_kompetensi,
				a.kreatifitas_2::integer * 10 as score_kreatifitas,
				a.konsistensi_2::integer * 10 as score_konsistensi,

				a.total_score as total_score,
				a.nilai_akhir as nilai_akhir,a.keterangan_nilai_akhir,a.kekuatan_karyawan,a.kekurangan_karyawan,a.kebutuhan_training
				
				from dym_performance_appraisal_form_a a
				left join hr_employee he on he.id = a.employee_id
				left join hr_employee he_1 on he_1.id = a.atasan_1
				left join hr_employee he_2 on he_2.id = a.atasan_2
				left join hr_department dep on dep.id = he.department_id
				where  a.state in ('atasan1_answer','atasan2_answer','posted') """ + where_department + """ """ + where_periode + """  order by dep.name,he.name
					"""
		else:
			nama_sheet = "Report PK Form B"
			if department_ids:
				where_department = " and dep.id in %s"% str(tuple(department_ids)).replace(',)', ')')
			if start_date:
				where_start_date = " and b.date >= '%s'"% str(start_date)
			if end_date:
				where_end_date = " and b.date <= '%s'"% str(end_date)
			if periode:
				where_periode = " and b.periode = '%s'"% str(periode)
			query= """ select he.name as karyawan,he.barcode as nik,dep.loc as cabang,dep.name as department_name,
				case when b.state = 'draft' then 'Draft'
					when b.state = 'start' then 'Start'
					when b.state = 'employee_answer' then 'Employee Answered'
					when b.state = 'atasan1_answer' then 'Atasan 1 Answered'
					when b.state = 'atasan2_answer' then 'Atasan 2 Answered'
					when b.state = 'posted' then 'Posted'
					when b.state = 'cancel' then 'Cancel' end as state,
				b.kualitas as kualitas_employee,
				b.kuantitas as kuantitas_employee,
				b.kerjasama as kerjasama_employee,
				b.disiplin as disiplin_employee,
				b.kompetensi as kompetensi_employee,
				b.kreatifitas as kreatifitas_employee,
				b.konsistensi as konsistensi_employee,
				b.kepemimpinan as kepemimpinan_employee,

				he_1.name as atasan_1,
				b.kualitas_1 as kualitas_atasan1,
				b.kuantitas_1 as kuantitas_atasan1,
				b.kerjasama_1 as kerjasama_atasan1,
				b.disiplin_1 as disiplin_atasan1,
				b.kompetensi_1 as kompetensi_atasan1,
				b.kreatifitas_1 as kreatifitas_atasan1,
				b.konsistensi_1 as konsistensi_atasan1,
				b.kepemimpinan_1 as kepemimpinan_atasan1,

				he_2.name as atasan_2,
				b.kualitas_2 as kualitas_atasan2,
				b.kuantitas_2 as kuantitas_atasan2,
				b.kerjasama_2 as kerjasama_atasan2,
				b.disiplin_2 as disiplin_atasan2,
				b.kompetensi_2 as kompetensi_atasan2,
				b.kreatifitas_2 as kreatifitas_atasan2,
				b.konsistensi_2 as konsistensi_atasan2,
				b.kepemimpinan_2 as kepemimpinan_atasan2,

				b.kualitas_2::integer * 15 as score_kualitas,
				b.kuantitas_2::integer * 15 as score_kuantitas,
				b.kerjasama_2::integer * 15 as score_kerjasama,
				b.disiplin_2::integer * 10 as score_disiplin,
				b.kompetensi_2::integer * 10 as score_kompetensi,
				b.kreatifitas_2::integer * 10 as score_kreatifitas,
				b.konsistensi_2::integer * 10 as score_konsistensi,
				b.kepemimpinan_2::integer * 15 as score_kepemimpinan,

				b.total_score as total_score,
				b.nilai_akhir as nilai_akhir,b.keterangan_nilai_akhir,b.kekuatan_karyawan,b.kekurangan_karyawan,b.kebutuhan_training
				
				from dym_performance_appraisal_form_b b
				left join hr_employee he on he.id = b.employee_id
				left join hr_employee he_1 on he_1.id = b.atasan_1
				left join hr_employee he_2 on he_2.id = b.atasan_2
				left join hr_department dep on dep.id = he.department_id 
				where  b.state in ('atasan1_answer','atasan2_answer','posted') """ + where_department + """ """ + where_periode + """  order by dep.name,he.name
			"""

		self._cr.execute(query)
		all_lines = self._cr.dictfetchall()
		
		datas=[]
		if all_lines:
			for x in all_lines:
				datas.append(x)

		row = 0
		col = 0

		_logger.info(datas)
		sheet = workbook.add_worksheet(nama_sheet)
		bold = workbook.add_format({'bold': True})
		cell_format_int = workbook.add_format({'align': 'center',
									 'valign': 'vcenter'})
		cell_format_int.set_num_format(1) 
		header_format = workbook.add_format({'bold': True,
									 'align': 'center',
									 'valign': 'vcenter',
									 'fg_color': '#fff89e',
									 'border': 1})
		center_format = workbook.add_format({'align': 'center',
									 'valign': 'vcenter'})

		if tipe_report == 'form_b':
			sheet.set_column('B:AS', 30)
			sheet.set_row(row + 3, 30)

			sheet.write(row, 0, nama_sheet + ' Atasan 1 Answered to Posted', bold)
			sheet.write(row + 1, 0, 'Periode : %s' %(periode))
			sheet.write(row + 3, 0, 'No.', header_format)
			sheet.write(row + 3, 1, 'Karyawan', header_format)
			sheet.write(row + 3, 2, 'Lokasi', header_format)
			sheet.write(row + 3, 3, 'NIK', header_format)
			sheet.write(row + 3, 4, 'Department', header_format)
			sheet.write(row + 3, 5, 'Kualitas Employee', header_format)
			sheet.write(row + 3, 6, 'Kuantitas Employee', header_format)
			sheet.write(row + 3, 7, 'Kerjasama Employee', header_format)
			sheet.write(row + 3, 8, 'Disiplin Employee', header_format)
			sheet.write(row + 3, 9, 'Kompetensi Employee', header_format)
			sheet.write(row + 3, 10, 'Kreatifitas Employee', header_format)
			sheet.write(row + 3, 11, 'Konsistensi Employee', header_format)
			sheet.write(row + 3, 12, 'Kepemimpinan Employee', header_format)
			sheet.write(row + 3, 13, 'Atasan 1', header_format)
			sheet.write(row + 3, 14, 'Kualitas Atasan 1', header_format)
			sheet.write(row + 3, 15, 'Kuantitas Atasan 1', header_format)
			sheet.write(row + 3, 16, 'Kerjasama Atasan 1', header_format)
			sheet.write(row + 3, 17, 'Disiplin Atasan 1', header_format)
			sheet.write(row + 3, 18, 'Kompetensi Atasan 1', header_format)
			sheet.write(row + 3, 19, 'Kreatifitas Atasan 1', header_format)
			sheet.write(row + 3, 20, 'Konsistensi Atasan 1', header_format)
			sheet.write(row + 3, 21, 'Kepemimpinan Atasan 1', header_format)
			sheet.write(row + 3, 22, 'Atasan 2', header_format)
			sheet.write(row + 3, 23, 'Kualitas Atasan 2', header_format)
			sheet.write(row + 3, 24, 'Kuantitas Atasan 2', header_format)
			sheet.write(row + 3, 25, 'Kerjasama Atasan 2', header_format)
			sheet.write(row + 3, 26, 'Disiplin Atasan 2', header_format)
			sheet.write(row + 3, 27, 'Kompetensi Atasan 2', header_format)
			sheet.write(row + 3, 28, 'Kreatifitas Atasan 2', header_format)
			sheet.write(row + 3, 29, 'Konsistensi Atasan 2', header_format)
			sheet.write(row + 3, 30, 'Kepemimpinan Atasan 2', header_format)
			sheet.write(row + 3, 31, 'Score Kualitas', header_format)
			sheet.write(row + 3, 32, 'Score Kuantitas', header_format)
			sheet.write(row + 3, 33, 'Score Kerjasama', header_format)
			sheet.write(row + 3, 34, 'Score Disiplin', header_format)
			sheet.write(row + 3, 35, 'Score Kompetensi', header_format)
			sheet.write(row + 3, 36, 'Score Kreatifitas', header_format)
			sheet.write(row + 3, 37, 'Score Konsistensi', header_format)
			sheet.write(row + 3, 38, 'Score Kepemimpinan', header_format)
			sheet.write(row + 3, 39, 'Kekuatan Karyawan', header_format)
			sheet.write(row + 3, 40, 'Kekurangan Karyawan', header_format)
			sheet.write(row + 3, 41, 'Kebutuhan Training', header_format)
			sheet.write(row + 3, 42, 'Total Score', header_format)
			sheet.write(row + 3, 43, 'Nilai Akhir', header_format)
			sheet.write(row + 3, 44, 'Ket Nilai Akhir', header_format)

			row = 4
			no = 1
			if datas:
				for x in datas:
					sheet.write(row, 0, no, center_format)
					sheet.write(row, 1, x['karyawan'])
					sheet.write(row, 2, x['cabang'])
					sheet.write(row, 3, x['nik'])
					sheet.write(row, 4, x['department_name'])
					sheet.write(row, 5, x['kualitas_employee'], center_format)
					sheet.write(row, 6, x['kuantitas_employee'], center_format)
					sheet.write(row, 7, x['kerjasama_employee'], center_format)
					sheet.write(row, 8, x['disiplin_employee'], center_format)
					sheet.write(row, 9, x['kompetensi_employee'], center_format)
					sheet.write(row, 10, x['kreatifitas_employee'], center_format)
					sheet.write(row, 11, x['konsistensi_employee'], center_format)
					sheet.write(row, 12, x['kepemimpinan_employee'], center_format)
					sheet.write(row, 13, x['atasan_1'], center_format)
					sheet.write(row, 14, x['kualitas_atasan1'], center_format)
					sheet.write(row, 15, x['kuantitas_atasan1'], center_format)
					sheet.write(row, 16, x['kerjasama_atasan1'], center_format)
					sheet.write(row, 17, x['disiplin_atasan1'], center_format)
					sheet.write(row, 18, x['kompetensi_atasan1'], center_format)
					sheet.write(row, 19, x['kreatifitas_atasan1'], center_format)
					sheet.write(row, 20, x['konsistensi_atasan1'], center_format)
					sheet.write(row, 21, x['kepemimpinan_atasan1'], center_format)
					sheet.write(row, 22, x['atasan_2'], center_format)
					sheet.write(row, 23, x['kualitas_atasan2'], center_format)
					sheet.write(row, 24, x['kuantitas_atasan2'], center_format)
					sheet.write(row, 25, x['kerjasama_atasan2'], center_format)
					sheet.write(row, 26, x['disiplin_atasan2'], center_format)
					sheet.write(row, 27, x['kompetensi_atasan2'], center_format)
					sheet.write(row, 28, x['kreatifitas_atasan2'], center_format)
					sheet.write(row, 29, x['konsistensi_atasan2'], center_format)
					sheet.write(row, 30, x['kepemimpinan_atasan2'], center_format)
					sheet.write(row, 31, x['score_kualitas'], center_format)
					sheet.write(row, 32, x['score_kuantitas'], center_format)
					sheet.write(row, 33, x['score_kerjasama'], center_format)
					sheet.write(row, 34, x['score_disiplin'], center_format)
					sheet.write(row, 35, x['score_kompetensi'], center_format)
					sheet.write(row, 36, x['score_kreatifitas'], center_format)
					sheet.write(row, 37, x['score_konsistensi'], center_format)
					sheet.write(row, 38, x['score_kepemimpinan'], center_format)
					sheet.write(row, 39, x['kekuatan_karyawan'], center_format)
					sheet.write(row, 40, x['kekurangan_karyawan'], center_format)
					sheet.write(row, 41, x['kebutuhan_training'], center_format)
					sheet.write(row, 42, x['total_score'], center_format)
					sheet.write(row, 43, x['nilai_akhir'], center_format)
					sheet.write(row, 44, x['keterangan_nilai_akhir'], center_format)

					row += 1
					no += 1

				sheet.write(row, 0, None)
				sheet.write(row + 1, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
			else:
				sheet.write(row, 0, 'No Data Found')
				sheet.write(row + 2, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
		else:
			sheet.set_column('B:AO', 30)
			sheet.set_row(row + 3, 30)

			sheet.write(row, 0, nama_sheet + ' Atasan 1 Answered to Posted', bold)
			sheet.write(row + 1, 0, 'Periode : %s' %(periode))
			sheet.write(row + 3, 0, 'No.', header_format)
			sheet.write(row + 3, 1, 'Karyawan', header_format)
			sheet.write(row + 3, 2, 'Lokasi', header_format)
			sheet.write(row + 3, 3, 'NIK', header_format)
			sheet.write(row + 3, 4, 'Department', header_format)
			sheet.write(row + 3, 5, 'Kualitas Employee', header_format)
			sheet.write(row + 3, 6, 'Kuantitas Employee', header_format)
			sheet.write(row + 3, 7, 'Kerjasama Employee', header_format)
			sheet.write(row + 3, 8, 'Disiplin Employee', header_format)
			sheet.write(row + 3, 9, 'Kompetensi Employee', header_format)
			sheet.write(row + 3, 10, 'Kreatifitas Employee', header_format)
			sheet.write(row + 3, 11, 'Konsistensi Employee', header_format)
			sheet.write(row + 3, 12, 'Atasan 1', header_format)
			sheet.write(row + 3, 13, 'Kualitas Atasan 1', header_format)
			sheet.write(row + 3, 14, 'Kuantitas Atasan 1', header_format)
			sheet.write(row + 3, 15, 'Kerjasama Atasan 1', header_format)
			sheet.write(row + 3, 16, 'Disiplin Atasan 1', header_format)
			sheet.write(row + 3, 17, 'Kompetensi Atasan 1', header_format)
			sheet.write(row + 3, 18, 'Kreatifitas Atasan 1', header_format)
			sheet.write(row + 3, 19, 'Konsistensi Atasan 1', header_format)
			sheet.write(row + 3, 20, 'Atasan 2', header_format)
			sheet.write(row + 3, 21, 'Kualitas Atasan 2', header_format)
			sheet.write(row + 3, 22, 'Kuantitas Atasan 2', header_format)
			sheet.write(row + 3, 23, 'Kerjasama Atasan 2', header_format)
			sheet.write(row + 3, 24, 'Disiplin Atasan 2', header_format)
			sheet.write(row + 3, 25, 'Kompetensi Atasan 2', header_format)
			sheet.write(row + 3, 26, 'Kreatifitas Atasan 2', header_format)
			sheet.write(row + 3, 27, 'Konsistensi Atasan 2', header_format)
			sheet.write(row + 3, 28, 'Score Kualitas', header_format)
			sheet.write(row + 3, 29, 'Score Kuantitas', header_format)
			sheet.write(row + 3, 30, 'Score Kerjasama', header_format)
			sheet.write(row + 3, 31, 'Score Disiplin', header_format)
			sheet.write(row + 3, 32, 'Score Kompetensi', header_format)
			sheet.write(row + 3, 33, 'Score Kreatifitas', header_format)
			sheet.write(row + 3, 34, 'Score Konsistensi', header_format)
			sheet.write(row + 3, 35, 'Kekuatan Karyawan', header_format)
			sheet.write(row + 3, 36, 'Kekurangan Karyawan', header_format)
			sheet.write(row + 3, 37, 'Kebutuhan Training', header_format)
			sheet.write(row + 3, 38, 'Total Score', header_format)
			sheet.write(row + 3, 39, 'Nilai Akhir', header_format)
			sheet.write(row + 3, 40, 'Ket Nilai Akhir', header_format)

			row = 4
			no = 1
			if datas:
				for x in datas:
					sheet.write(row, 0, no, center_format)
					sheet.write(row, 1, x['karyawan'])
					sheet.write(row, 2, x['cabang'])
					sheet.write(row, 3, x['nik'])
					sheet.write(row, 4, x['department_name'])
					sheet.write(row, 5, x['kualitas_employee'], center_format)
					sheet.write(row, 6, x['kuantitas_employee'], center_format)
					sheet.write(row, 7, x['kerjasama_employee'], center_format)
					sheet.write(row, 8, x['disiplin_employee'], center_format)
					sheet.write(row, 9, x['kompetensi_employee'], center_format)
					sheet.write(row, 10, x['kreatifitas_employee'], center_format)
					sheet.write(row, 11, x['konsistensi_employee'], center_format)
					sheet.write(row, 12, x['atasan_1'], center_format)
					sheet.write(row, 13, x['kualitas_atasan1'], center_format)
					sheet.write(row, 14, x['kuantitas_atasan1'], center_format)
					sheet.write(row, 15, x['kerjasama_atasan1'], center_format)
					sheet.write(row, 16, x['disiplin_atasan1'], center_format)
					sheet.write(row, 17, x['kompetensi_atasan1'], center_format)
					sheet.write(row, 18, x['kreatifitas_atasan1'], center_format)
					sheet.write(row, 19, x['konsistensi_atasan1'], center_format)
					sheet.write(row, 20, x['atasan_2'], center_format)
					sheet.write(row, 21, x['kualitas_atasan2'], center_format)
					sheet.write(row, 22, x['kuantitas_atasan2'], center_format)
					sheet.write(row, 23, x['kerjasama_atasan2'], center_format)
					sheet.write(row, 24, x['disiplin_atasan2'], center_format)
					sheet.write(row, 25, x['kompetensi_atasan2'], center_format)
					sheet.write(row, 26, x['kreatifitas_atasan2'], center_format)
					sheet.write(row, 27, x['konsistensi_atasan2'], center_format)
					sheet.write(row, 28, x['score_kualitas'], center_format)
					sheet.write(row, 29, x['score_kuantitas'], center_format)
					sheet.write(row, 30, x['score_kerjasama'], center_format)
					sheet.write(row, 31, x['score_disiplin'], center_format)
					sheet.write(row, 32, x['score_kompetensi'], center_format)
					sheet.write(row, 33, x['score_kreatifitas'], center_format)
					sheet.write(row, 34, x['score_konsistensi'], center_format)
					sheet.write(row, 35, x['kekuatan_karyawan'], center_format)
					sheet.write(row, 36, x['kekurangan_karyawan'], center_format)
					sheet.write(row, 37, x['kebutuhan_training'], center_format)
					sheet.write(row, 38, x['total_score'], center_format)
					sheet.write(row, 39, x['nilai_akhir'], center_format)
					sheet.write(row, 40, x['keterangan_nilai_akhir'], center_format)

					row += 1
					no += 1

				sheet.write(row, 0, None)
				sheet.write(row + 1, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
			else:
				sheet.write(row, 0, 'No Data Found')
				sheet.write(row + 2, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))