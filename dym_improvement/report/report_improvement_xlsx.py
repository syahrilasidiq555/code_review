from odoo import models, exceptions, _
import time
import logging
from odoo.exceptions import MissingError, UserError, ValidationError


class report_improvement_xlsx(models.AbstractModel):
    _name = 'report.dym_improvement.report_improvement'
    _inherit = 'report.report_xlsx.abstract'

    def get_data(self, start_date, end_date, department_ids,level,jenis_improvement,state_improvement):
        _logger = logging.getLogger(__name__)

        where_start_date = " 1=1 "
        if start_date:
            where_start_date = " i.bulan_pendaftaran >= '%s' " % str(start_date)
        where_end_date = " 1=1 "
        if end_date:
            where_end_date = " i.bulan_pendaftaran <= '%s' " % str(end_date)

        where_dept_id = " 1=1 "
        if department_ids:
            where_dept_id = " d.id in %s " % str(tuple(department_ids)).replace(',)', ')')

        where_jenis_improvement = " 1=1 "
        if jenis_improvement:
            where_jenis_improvement = " i.jenis_improvement = '%s' " % str(jenis_improvement)
        
        where_state_improvement = " 1=1 "
        if state_improvement:
            where_state_improvement = " i.state_improvement = '%s' " % str(state_improvement)

        where_level = " 1=1 "
        if level:
            where_level = " i.level = '%s' " % str(level)
        

        report_improvement = {
            'type': 'Track',
            'title': '',
            'title_short': ''}

        query = """
            select 
                i.name as improvement_name,
                CASE when i.jenis_improvement = 'qcc' then 'QCC'
                    when i.jenis_improvement = 'qcp' then 'QCP'
                    when i.jenis_improvement = 'pps' then 'PPS'
                    when i.jenis_improvement = 'qcl' then 'QCL'
                    when i.jenis_improvement = 'pps' then 'PPS'
                    when i.jenis_improvement = 'fiver' then '5R'
                    when i.jenis_improvement = 'safety_improvement' then 'Safety Improvement'
                end jenis_improvement,
                to_char(i.bulan_pendaftaran, 'DD/MM/YYYY') as bulan_pendaftaran,
                to_char(date(i.create_date), 'DD/MM/YYYY') as tgl_dibuat,
                i.team_name as team_name,
                e.name as pic,
                di.member_list as member_list,
                string_agg(d.name,', ') as departments,
                i.tema_improvement as tema_improvement,
                i.deskripsi_plan as deskripsi_plan,
                i.loc_improvement as loc_improvement,
                i.total_cost as total_cost,
                i.total_benefit as total_benefit,
                i.ratio_percentage as ratio_percentage,
                step.name as state_improvement,
                CASE when i.state = 'new' then 'NEW'
                    when i.state = 'in_progress' then 'IN PROGRESS'
                    when i.state = 'revise' then 'REVISED'
                    when i.state = 'refuse' then 'REFUSED'
                    when i.state = 'rfa' then 'REQUEST FOR APPROVAL'
                    when i.state = 'done' then 'DONE'
                end state,
                to_char(date(impal.tanggal), 'DD/MM/YYYY') as last_approval,
                CASE when i.level = 'bronze' then 'BRONZE'
                    when i.level = 'silver' then 'SILVER'
                    when i.level = 'gold' then 'GOLD'
                end level_improvement

            from dym_improvement i
            left join improvement_step step on step.id = i.step_id
            left join hr_employee e on i.pic = e.id
            inner join improvement_departments_rel idr on idr.improvement_id = i.id
            inner join hr_department d on d.id = idr.department_id 
            left join (
                select i.id as id, string_agg(em.name,', ') as member_list from dym_improvement i
                inner join improvement_users_rel iur on iur.imp_id = i.id
                inner join res_users u on iur.team_id = u.id
                inner join hr_employee em on em.user_id = u.id
                group by i.id
            )di on di.id = i.id
            left join (
                select distinct imp_id, max(tanggal) as tanggal from dym_improvement_approval_line group by imp_id
            ) impal on impal.imp_id = i.id

            where """+where_dept_id+"""
            and """+where_start_date+"""
            and """+where_end_date  +"""
            and """+where_jenis_improvement+"""
            and """+where_state_improvement+"""
            and """+where_level+"""

            group by 
                improvement_name, 
                step.name,
                i.jenis_improvement,
                bulan_pendaftaran,
                tgl_dibuat, 
                team_name, 
                e.name, 
                tema_improvement, 
                deskripsi_plan, 
                loc_improvement,
                total_cost, 
                total_benefit, 
                ratio_percentage, 
                state,
                last_approval,
                level_improvement,
                member_list
        """
        reports = [report_improvement]

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
                        'improvement_name': str(x['improvement_name'].encode('ascii', 'ignore').decode('ascii')) if x['improvement_name'] != None else '',
                        'jenis_improvement': str(x['jenis_improvement']) if x['jenis_improvement'] != None else '',
                        'bulan_pendaftaran': str(x['bulan_pendaftaran']) if x['bulan_pendaftaran'] != None else '',
                        'team_name': str(x['team_name']) if x['team_name'] != None else '',
                        'pic': str(x['pic']) if x['pic'] != None else '',
                        'member_list': str(x['member_list']) if x['member_list'] != None else '',
                        'departments': str(x['departments']) if x['departments'] != None else '',
                        'tema_improvement': str(x['tema_improvement']) if x['tema_improvement'] != None else '',
                        'deskripsi_plan': str(x['deskripsi_plan']) if x['deskripsi_plan'] != None else '',
                        'loc_improvement': str(x['loc_improvement']) if x['loc_improvement'] != None else '',
                        'total_cost': float(x['total_cost']) if x['total_cost'] != None else 0,
                        'total_benefit': float(x['total_benefit']) if x['total_benefit'] != None else 0,
                        'ratio_percentage': str(x['ratio_percentage']) if x['ratio_percentage'] != None else '',
                        'state_improvement': str(x['state_improvement']) if x['state_improvement'] != None else '',
                        'state': str(x['state']) if x['state'] != None else '',
                        'last_approval': str(x['last_approval']) if x['last_approval'] != None else '',
                        'level_improvement': str(x['level_improvement']) if x['level_improvement'] != None else '',
                        'tgl_dibuat': str(x['tgl_dibuat']) if x['tgl_dibuat'] != None else ''
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
        level = data.get('level')
        jenis_improvement = data.get('jenis_improvement')
        state_improvement = data.get('state_improvement')


        datas = self.get_data(start_date, end_date, department_ids,level,jenis_improvement,state_improvement)

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
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 30)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:H', 40)
        sheet.set_column('I:I', 30)
        sheet.set_column('J:J', 40)
        sheet.set_column('K:K', 20)
        sheet.set_column('L:N', 15)
        sheet.set_column('O:O', 35)
        sheet.set_column('O:O', 35)
        sheet.set_column('P:P', 20)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 10)





        sheet.set_row(row + 3, 30)

        sheet.write(row, 0, 'Report QCC, QCP, PPS, 5R, Safety Improvement', bold)
        sheet.write(row + 1, 0, 'Tanggal : %s - %s' % (start_date, end_date))
        sheet.write(row + 3, 0, 'No.', header_format)
        sheet.write(row + 3, 1, 'Improvement Name', header_format)
        sheet.write(row + 3, 2, 'Jenis Improvement', header_format)
        sheet.write(row + 3, 3, 'Bulan Pendaftaran', header_format)
        sheet.write(row + 3, 4, 'Team Name', header_format)
        sheet.write(row + 3, 5, 'PIC', header_format)
        sheet.write(row + 3, 6, 'Member List', header_format)
        sheet.write(row + 3, 7, 'Department List', header_format)
        sheet.write(row + 3, 8, 'Tema Improvement', header_format)
        sheet.write(row + 3, 9, 'Deskripsi', header_format)
        sheet.write(row + 3, 10, 'Lokasi Improvement', header_format)
        sheet.write(row + 3, 11, 'Total Cost', header_format)
        sheet.write(row + 3, 12, 'Total Benefit', header_format)
        sheet.write(row + 3, 13, 'Ratio Percentage', header_format)
        sheet.write(row + 3, 14, 'State Improvement', header_format)
        sheet.write(row + 3, 15, 'State', header_format)
        sheet.write(row + 3, 16, 'Last Approval', header_format)
        sheet.write(row + 3, 17, 'Level', header_format)
        sheet.write(row + 3, 18, 'Tanggal Dibuat', header_format)
        row += 4
        no = 1

        if datas:
            for x in datas:
                # _logger.info('OBJ '+str(x))

                sheet.write(row, 0, no, center_format)
                sheet.write(row, 1, x['improvement_name'])
                sheet.write(row, 2, x['jenis_improvement'])
                sheet.write(row, 3, x['bulan_pendaftaran'],center_format)
                sheet.write(row, 4, x['team_name'])
                sheet.write(row, 5, x['pic'])
                sheet.write(row, 6, x['member_list'])
                sheet.write(row, 7, x['departments'])
                sheet.write(row, 8, x['tema_improvement'])
                sheet.write(row, 9, x['deskripsi_plan'])
                sheet.write(row, 10, x['loc_improvement'])
                sheet.write(row, 11, x['total_cost'], right_format)
                sheet.write(row, 12, x['total_benefit'], right_format)
                sheet.write(row, 13, x['ratio_percentage'], right_format)
                sheet.write(row, 14, x['state_improvement'])
                sheet.write(row, 15, x['state'])
                sheet.write(row, 16, x['last_approval'],center_format)
                sheet.write(row, 17, x['level_improvement'])
                sheet.write(row, 18, x['tgl_dibuat'],center_format)


                row += 1
                no += 1

            sum_total_cost = '=SUM(L5:L'+str(row)+')'
            sum_total_benefit = '=SUM(M5:M'+str(row)+')'
            

            for i in range(0,11):
                sheet.write(row,i, None, footer_format)

            sheet.write(row,11, sum_total_cost, footer_format)
            sheet.write(row,12, sum_total_benefit, footer_format)

            for x in range(13,19):
                sheet.write(row,x, None, footer_format)
            

            sheet.write(row + 1 , 0, None)
            sheet.write(row + 2, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
        else:
            sheet.write(row, 0, 'No Data Found')
            sheet.write(row + 3, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))