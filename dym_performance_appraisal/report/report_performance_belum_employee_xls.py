from odoo import models, exceptions, _, osv
import time
import logging 
from odoo.exceptions import MissingError
from datetime import datetime,timedelta

class report_performance_belum_employee_xls(models.AbstractModel):
	_name = 'report.dym_performance_appraisal.report_belum_employee_xls'
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
				select he.name as employee_name,he.barcode nik ,j.name as job,he1.name as atasan, dep.name as dept_name,dep.loc as cabang,
                    case when a.state = 'draft' then 'Draft'
                                        when a.state = 'start' then 'Start'
                                        when a.state = 'employee_answer' then 'Employee Answered'
                                        when a.state = 'atasan1_answer' then 'Atasan 1 Answered'
                                        when a.state = 'atasan2_answer' then 'Atasan 2 Answered'
                                        when a.state = 'posted' then 'Posted'
                                        when a.state = 'cancel' then 'Cancel' end as state
                    from hr_employee he left join hr_job j on j.id = he.job_id
                    left join dym_performance_appraisal_form_a a on a.employee_id = he.id and a.state != 'cancel' """ + where_periode + """ 
                    left join hr_employee he1 on he1.id = he.parent_id
                    left join hr_department dep on dep.id = he.department_id
                    where he.active = 't' 
                    and j.name in ('SECURITY','PART DEPO ADMIN','MECHANIC TRAINEE','MECHANIC REPAIR 2','MECHANIC REPAIR 1','OFFICE BOY','COURIER','PART INVENTORY OFFICER','PDI MECHANIC','PART CONTROL','DRIVER','PART SALESMAN','CO DRIVER','WORKSHOP ADMINISTRATION','COUNTER SPAREPART','CASHIER','MARKETING','MARKETING COUNTER','STNK ADMINISTRATION','SALES ADMINISTRATION','MECHANIC REPAIR 3','CASHIER AHASS')
                    and (a.state in ('draft','start','employee_answer') or a.state is null) """ + where_department + """ 
                    order by dep.name,he.name,a.state
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
			query= """ 
            select he.name as employee_name,he.barcode nik,j.name as job,he1.name as atasan, dep.name as dept_name,dep.loc as cabang,
                case when b.state = 'draft' then 'Draft'
                                    when b.state = 'start' then 'Start'
                                    when b.state = 'employee_answer' then 'Employee Answered'
                                    when b.state = 'atasan1_answer' then 'Atasan 1 Answered'
                                    when b.state = 'atasan2_answer' then 'Atasan 2 Answered'
                                    when b.state = 'posted' then 'Posted'
                                    when b.state = 'cancel' then 'Cancel' end as state
                from hr_employee he left join hr_job j on j.id = he.job_id
                left join dym_performance_appraisal_form_b b on b.employee_id = he.id and b.state != 'cancel' """ + where_periode + """ 
                left join hr_employee he1 on he1.id = he.parent_id
                left join hr_department dep on dep.id = he.department_id
                where he.active = 't' 
                and j.name in ('MARKETING SUPERVISOR','MECHANIC HEAD','SERVICE ADVISOR')
                and (b.state in ('draft','start','employee_answer') or b.state is null) """ + where_department + """
                order by dep.name,he.name,b.state
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
			sheet.set_column('B:I', 30)
			sheet.set_row(row + 3, 30)

			sheet.write(row, 0, nama_sheet + ' Belum Answer to Employee Answered', bold)
			sheet.write(row + 1, 0, 'Periode : %s' %(periode))
			sheet.write(row + 3, 0, 'No.', header_format)
			sheet.write(row + 3, 1, 'Karyawan', header_format)
			sheet.write(row + 3, 2, 'NIK', header_format)
			sheet.write(row + 3, 3, 'Pekerjaan', header_format)
			sheet.write(row + 3, 4, 'Atasan', header_format)
			sheet.write(row + 3, 5, 'Department', header_format)
			sheet.write(row + 3, 6, 'Lokasi', header_format)
			sheet.write(row + 3, 7, 'Status PK', header_format)

			row = 4
			no = 1
			if datas:
				for x in datas:
					sheet.write(row, 0, no, center_format)
					sheet.write(row, 1, x['employee_name'])
					sheet.write(row, 2, x['nik'])
					sheet.write(row, 3, x['job'])
					sheet.write(row, 4, x['atasan'])
					sheet.write(row, 5, x['dept_name'], center_format)
					sheet.write(row, 6, x['cabang'], center_format)
					sheet.write(row, 7, x['state'], center_format)

					row += 1
					no += 1

				sheet.write(row, 0, None)
				sheet.write(row + 1, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
			else:
				sheet.write(row, 0, 'No Data Found')
				sheet.write(row + 2, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
		else:
			sheet.set_column('B:I', 30)
			sheet.set_row(row + 3, 30)

			sheet.write(row, 0, nama_sheet + ' Belum Answer to Employee Answered', bold)
			sheet.write(row + 1, 0, 'Periode : %s' %(periode))
			sheet.write(row + 3, 0, 'No.', header_format)
			sheet.write(row + 3, 1, 'Karyawan', header_format)
			sheet.write(row + 3, 2, 'NIK', header_format)
			sheet.write(row + 3, 3, 'Pekerjaan', header_format)
			sheet.write(row + 3, 4, 'Atasan', header_format)
			sheet.write(row + 3, 5, 'Department', header_format)
			sheet.write(row + 3, 6, 'Lokasi', header_format)
			sheet.write(row + 3, 7, 'Status PK', header_format)

			row = 4
			no = 1
			if datas:
				for x in datas:
					sheet.write(row, 0, no, center_format)
					sheet.write(row, 1, x['employee_name'])
					sheet.write(row, 2, x['nik'])
					sheet.write(row, 3, x['job'])
					sheet.write(row, 4, x['atasan'])
					sheet.write(row, 5, x['dept_name'], center_format)
					sheet.write(row, 6, x['cabang'], center_format)
					sheet.write(row, 7, x['state'], center_format)

					row += 1
					no += 1

				sheet.write(row, 0, None)
				sheet.write(row + 1, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
			else:
				sheet.write(row, 0, 'No Data Found')
				sheet.write(row + 2, 0, (datetime.now()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))