from odoo import models, exceptions, _
import time
import logging
from odoo.exceptions import MissingError, UserError, ValidationError
from datetime import datetime, timedelta

class report_attendance_emp_terlambat(models.AbstractModel):
    _name = 'report.hr_attendance.report_attendance_emp_terlambat'
    _inherit = 'report.report_xlsx.abstract'

    def get_data(self, start_date, end_date, department_ids):
        _logger = logging.getLogger(__name__)

        where_department_ids = " 1=1 "
        if department_ids:
            where_department_ids =  " d.id in %s " % str(tuple(department_ids)).replace(',)', ')')


        date_start = start_date if start_date else ''
        date_end = end_date if end_date else ''

        report_terlambat = {
            'type': 'Track',
            'title': '',
            'title_short': ''}


        query = """ 
            select
                d.name as department,
                s.name as section,
                e.barcode as nik,
                e.name as nama,
                j.name as position,
                count(t.attendance_id) as total_terlambat,
                hk.hari_kerja as hr_kerja,
                --coalesce(off.total_off,0) as total_off,
                hk.hari_kerja - 0 as hari_kerja
            from hr_employee e
            left join hr_job j on j.id = e.job_id
            left join hr_department d on d.id = e.department_id
            left join hr_department s on s.id = e.section
            left join (
                select
                    rc.id as rc_id,
                    count(dt.datetime) as hari_kerja
                from resource_calendar rc
                left join (
                    select 
                        distinct on (rcl.calendar_id,rcl.dayofweek)
                        rcl.calendar_id as calendar_id,
                        rcl.dayofweek::integer as dayofweek
                    from resource_calendar_attendance rcl
                )rcl on rcl.calendar_id = rc.id
                inner join (
                    select dt.datetime as datetime, dt.dow as dow
                    from (
                        /*ambil data hari kerja yang tidak termasuk ke holiday*/
                        with gs as (
                            select 
                            generate_series('"""+str(date_start)+"""'::date, '"""+str(date_end)+"""'::date, '1 day') as datetime,
                            (extract(isodow from generate_series('"""+str(date_start)+"""'::date, '"""+str(date_end)+"""'::date, '1 day')) -1)::integer as dow
                        )
                        --select * from gs where datetime not in (select date from dym_master_holiday)
                        select * from gs where datetime not in (select date_from from resource_calendar_leaves)
                    ) dt
                )dt on dt.dow = rcl.dayofweek::integer
                group by rc.id
                order by rc.id
            )hk on hk.rc_id = e.resource_calendar_id

            left join (
                /* data terlambat individu */
                select 			
                    distinct on (a.employee_id, to_char(a.check_in + '7 hours' :: interval,'YYYY-MM-DD') )
                    a.id as attendance_id,
                    d.id as department_id,
                    e.id as employee_id,
                    e.name,
                    d.name,
                    to_char(a.check_in + '7 hours' :: interval,'YYYY-MM-DD') as date_checkin,
                    to_char(a.check_in + '7 hours' :: interval,'YYYY-MM-DD HH24:MI:SS') as check_in,	
                    to_number(to_char(a.check_in + '7 hours' :: interval,'hh24'),'99') as c_hour,
                    e.resource_calendar_id,
                    work_time.id
                    
                from hr_attendance a
                left join hr_employee e on e.id = a.employee_id
                left join hr_department d on d.id = e.department_id
                left join (
                    select rc.id as id, rcl.dayofweek, rcl.hour_to, rcl.hour_from from resource_calendar rc
                    left join resource_calendar_attendance rcl on rcl.calendar_id = rc.id
                    group by rc.id, rcl.dayofweek, rcl.hour_to, rcl.hour_from
                ) work_time on work_time.id = e.resource_calendar_id 
                and work_time.dayofweek = (extract(dow from a.check_in + '7 hours' :: interval) - 1)::varchar
                and ( work_time.hour_to <= to_number(to_char(a.check_in + '7 hours' :: interval,'hh24'),'99')
                or work_time.hour_from <= to_number(to_char(a.check_in + '7 hours' :: interval,'hh24'),'99'))

                where to_char(a.check_in+'7 hours'::interval,'YYYY-MM-DD') >= '"""+str(date_start)+"""'
                and to_char(a.check_in+'7 hours'::interval,'YYYY-MM-DD') <= '"""+str(date_end)+"""'
                and work_time.id is not null

                order by a.employee_id, date_checkin asc, a.id asc
            )t on employee_id = e.id
            
            
            where e.active = 't' and e.barcode is not null
            and """+where_department_ids+"""
            group by 
                d.name,
                s.name,
                e.barcode,
                e.name,
                j.name,
                hk.hari_kerja
            order by department,section,nama
        """


        reports = [report_terlambat]

        datas2 = []
        for report in reports:
            _logger.info(query)
            self._cr.execute(query)
            # print(query_start)
            all_lines = self._cr.dictfetchall()
            # _logger.debug('All Lines '+str(all_lines))
            items = []

            if all_lines:
                datas = map(
                    lambda x: {
                        'no': 0,
                        'department': str(x['department']) if x['department'] else '',
                        'section': str(x['section']) if x['section'] else '',
                        'nik': str(x['nik']) if x['nik'] else '',
                        'nama': str(x['nama']) if x['nama'] else '',
                        'position': str(x['position']) if x['position'] else '',
                        'total_terlambat': int(x['total_terlambat']) if x['total_terlambat'] else 0,
                        'hari_kerja': int(x['hari_kerja']) if x['hari_kerja'] else 0,

                    },

                    all_lines)
                # _logger.info('Report '+str(datas))
                for p in datas:
                    datas2.append(p)
                # _logger.info('Report '+str(datas2))
                # reports = filter(lambda x: datas, [{'datas': datas}])

                if datas2 != []:
                    return datas2

    def generate_xlsx_report(self, workbook, data, lines):
        # _logger = logging.getLogger(__name__)

        # _logger.info('DISINI ')
        # _logger.info('DISINA '+str(lines))
        # _logger.info('DISINE '+str(data.get('reports')))
        now = datetime.now() + timedelta(hours=7)
        department_ids = data.get('department_ids')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        datas = self.get_data(start_date, end_date, department_ids)

        row = 0
        col = 0

        sheet = workbook.add_worksheet("Report Employee Summary (Terlambat)")
        bold = workbook.add_format({'bold': True})
        cell_format_int = workbook.add_format({'align': 'center',
                                                'valign': 'vcenter'})
        cell_format_int.set_num_format(1)

        percent_with_decimal = workbook.add_format({'align': 'center',
                                                'valign': 'vcenter',
                                                'num_format': '#,##0.00%'})
        
        decimal_format = workbook.add_format({'align': 'center',
                                                'valign': 'vcenter',
                                                'num_format': '#,##0.00'})

        header_format = workbook.add_format({'bold': True,
                                            'align': 'center',
                                            'valign': 'vcenter',
                                            'fg_color': '#fff89e',
                                            'border': 1})
        center_format = workbook.add_format({'align': 'center',
                                            'valign': 'vcenter'})
        footer_format = workbook.add_format({'bold': True,
                                    'align': 'right',
                                    'valign': 'vcenter',
                                    'fg_color': '#fff89e'})

        sheet.set_column('B:C', 35)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 40)
        sheet.set_column('F:F', 35)
        sheet.set_column('G:I', 15)
        
        sheet.set_row(row + 3, 30)

        sheet.write(row, 0, 'Report Attendance Employee (Terlambat)', bold)
        sheet.write(row + 1, 0, 'Tanggal : %s - %s' % (start_date, end_date))
        sheet.write(row + 3, 0, 'No.', header_format)
        sheet.write(row + 3, 1, 'Department', header_format)
        sheet.write(row + 3, 2, 'Section', header_format)
        sheet.write(row + 3, 3, 'NIK', header_format)
        sheet.write(row + 3, 4, 'Nama', header_format)
        sheet.write(row + 3, 5, 'Posisi', header_format)
        sheet.write(row + 3, 6, 'Total Terlambat', header_format)
        sheet.write(row + 3, 7, 'Hari Kerja', header_format)
        sheet.write(row + 3, 8, 'Persentase (%)', header_format)


        row += 4
        no = 1

        if datas:
            for x in datas:
                sheet.write(row, 0, no, center_format)


                sheet.write(row, 1, x['department'])
                sheet.write(row, 2, x['section'])
                sheet.write(row, 3, x['nik'])
                sheet.write(row, 4, x['nama'])
                sheet.write(row, 5, x['position'])
                sheet.write(row, 6, x['total_terlambat'], cell_format_int)
                sheet.write(row, 7, x['hari_kerja'], cell_format_int)
                sheet.write(row, 8, '=(G'+str(row+1)+'/H'+str(row+1)+')', percent_with_decimal)

                row += 1
                no += 1

            sheet.write(row, 6,  '=SUM(G5:G'+str(row)+')', footer_format)
            sheet.write(row, 7,  '=SUM(H5:H'+str(row)+')', footer_format)
            sheet.write(row, 8,  '', footer_format)

            sheet.write(row, 0, None)
            sheet.write(row + 1, 0,
                        now.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
        else:
            sheet.write(row, 0, 'No Data Found')
            sheet.write(row + 2, 0,
                        now.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))