from odoo import models, exceptions, _
import time
import logging
from odoo.exceptions import MissingError, UserError, ValidationError


class report_improvement_dep_xlsx(models.AbstractModel):
    _name = 'report.dym_improvement.report_improvement_dep'
    _inherit = 'report.report_xlsx.abstract'

    def get_data(self, start_date, end_date, department_ids,jenis_improvement):
        _logger = logging.getLogger(__name__)

        where_start_date = " 1=1 "
        if start_date:
            where_start_date = " imp.bulan_pendaftaran >= '%s' " % str(start_date)
        where_end_date = " 1=1 "
        if end_date:
            where_end_date = " imp.bulan_pendaftaran <= '%s' " % str(end_date)

        where_dept_id = " 1=1 "
        if department_ids:
            where_dept_id = " d.id in %s " % str(tuple(department_ids)).replace(',)', ')')

        where_jenis_improvement = " 1=1 "
        if jenis_improvement:
            where_jenis_improvement = " imp.jenis_improvement = '%s' " % str(jenis_improvement)
        
        

        report_improvement_2 = {
            'type': 'Track',
            'title': '',
            'title_short': ''}

        query = """
            select 
                par.name as parent_divisi,
                dep.name as department,
                imp.bulan_pendaftaran as bulan_pendaftaran,
                upper(case when imp.jenis_improvement = 'fiver' then '5R' else replace(imp.jenis_improvement,'_',' ') end) as jenis_improvement,
                imp.total_ratio as nqi,
                case when imp.state != 'done' then step.name
                else 'Done' end as state_progress
                
            from dym_improvement imp
            left join hr_employee e on e.user_id = imp.create_uid
            left join hr_department dep on dep.id = e.department_id
            left join hr_department par on dep.parent_id = par.id
            left join improvement_step step on step.id = imp.step_id

            

            where dep.active = True
            and dep.name != 'CEO' 
            and """+where_dept_id+"""
            and """+where_start_date+"""
            and """+where_end_date  +"""
            and """+where_jenis_improvement+"""

            order by par.name,dep.name
        """
        reports = [report_improvement_2]

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
                        'parent_divisi':  str(x['parent_divisi']) if x['parent_divisi'] != None else '',
                        'department':  str(x['department']) if x['department'] != None else '',
                        'bulan_pendaftaran':  str(x['bulan_pendaftaran']) if x['bulan_pendaftaran'] != None else '',
                        'jenis_improvement':  str(x['jenis_improvement']) if x['jenis_improvement'] != None else '',
                        'nqi':  int(x['nqi']) if x['nqi'] != None else 0,
                        'state_progress':  str(x['state_progress']) if x['state_progress'] != None else '',
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
        department_ids = data.get('department_ids')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        jenis_improvement = data.get('jenis_improvement')


        datas = self.get_data(start_date, end_date, department_ids,jenis_improvement)

        row = 0
        col = 0

        sheet = workbook.add_worksheet("Report QCC QCP PPS dll")
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

        right_format = workbook.add_format({'align': 'right',
                                             'valign': 'vcenter'})
        footer_format = workbook.add_format({'bold': True,
                                    'align': 'right',
                                    'valign': 'vcenter',
                                    'fg_color': '#fff89e'})        
        sheet.set_column('B:C', 20)
        sheet.set_column('D:E', 17)
        sheet.set_column('F:F', 30)
        sheet.set_column('G:G', 20)


        sheet.set_row(row + 3, 30)

        sheet.write(row, 0, 'Report QCC, QCP, PPS, 5R, Safety Improvement', bold)
        sheet.write(row + 1, 0, 'Tanggal : %s - %s' % (start_date, end_date))
        sheet.write(row + 3, 0, 'No.', header_format)
        sheet.write(row + 3, 1, 'Area / Divisi', header_format)
        sheet.write(row + 3, 2, 'Department', header_format)
        sheet.write(row + 3, 3, 'Bulan Pendaftaran', header_format)
        sheet.write(row + 3, 4, 'Jenis Improvement', header_format)
        sheet.write(row + 3, 5, 'NQI', header_format)
        sheet.write(row + 3, 6, 'State/Step Progress', header_format)
        row += 4
        no = 1

        if datas:
            for x in datas:
                # _logger.info('OBJ '+str(x))

                sheet.write(row, 0, no, center_format)

                sheet.write(row, 1, x['parent_divisi'])
                sheet.write(row, 2, x['department'])
                sheet.write(row, 3, x['bulan_pendaftaran'], center_format)
                sheet.write(row, 4, x['jenis_improvement'])
                sheet.write(row, 5, x['nqi'], right_format)
                sheet.write(row, 6, x['state_progress'])


                row += 1
                no += 1

            sum_total_nqi = '=SUM(F5:F'+str(row)+')'
            

            for i in range(0,5):
                sheet.write(row,i, None, footer_format)

            sheet.write(row,5, sum_total_nqi, footer_format)
            sheet.write(row,6, None, footer_format)


            sheet.write(row + 1 , 0, None)
            sheet.write(row + 2, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
        else:
            sheet.write(row, 0, 'No Data Found')
            sheet.write(row + 3, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))