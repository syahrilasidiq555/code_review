from odoo import models, exceptions, _
import time
import logging
from odoo.exceptions import MissingError, UserError, ValidationError


class report_ss_tahunan_xlsx(models.AbstractModel):
    _name = 'report.report_dym_improvement.report_improvement_tahunan_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_data(self, state, tahun, department_ids, jenis_improvement, level):
        _logger = logging.getLogger(__name__)

        where_state = " 1=1 "
        if state:
            where_state = " imp.state = '%s' " % str(state)
        where_tahun = " 1=1 "
        if tahun:
            where_tahun = " to_char(imp.bulan_pendaftaran,'YYYY-MM-DD') >= '%s-01-01' " % str(tahun)

        where_department = " 1=1 "
        if department_ids:
            where_department = " d.id in %s " % str(tuple(department_ids)).replace(',)', ')')

        where_jenis_improvement = " 1=1 "
        if jenis_improvement:
            where_jenis_improvement = " imp.jenis_improvement = '%s' " % str(jenis_improvement)

        where_level = " 1=1 "
        if level:
            where_level = " imp.level = '%s' " % str(level)

        report_ss = {
            'type': 'Track',
            'title': '',
            'title_short': ''}

        query = """
            select
                par.name as parent,
                d.name as department,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '01' then 1 else 0 end) as januari,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '01' then i.total_ratio else 0 end) as nqi_jan,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '02' then 1 else 0 end) as februari,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '02' then i.total_ratio else 0 end) as nqi_feb,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '03' then 1 else 0 end) as maret,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '03' then i.total_ratio else 0 end) as nqi_mar,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '04' then 1 else 0 end) as april,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '04' then i.total_ratio else 0 end) as nqi_apr,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '05' then 1 else 0 end) as mei,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '05' then i.total_ratio else 0 end) as nqi_mei,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '06' then 1 else 0 end) as juni,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '06' then i.total_ratio else 0 end) as nqi_jun,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '07' then 1 else 0 end) as juli,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '07' then i.total_ratio else 0 end) as nqi_jul,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '08' then 1 else 0 end) as agustus,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '08' then i.total_ratio else 0 end) as nqi_ags,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '09' then 1 else 0 end) as september,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '09' then i.total_ratio else 0 end) as nqi_sep,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '10' then 1 else 0 end) as oktober,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '10' then i.total_ratio else 0 end) as nqi_okt,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '11' then 1 else 0 end) as november,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '11' then i.total_ratio else 0 end) as nqi_nov,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '12' then 1 else 0 end) as desember,
                sum(case when TO_CHAR(i.bulan_pendaftaran, 'MM') = '12' then i.total_ratio else 0 end) as nqi_des
            from hr_department d
            left join hr_department par on par.id = d.parent_id
            left join (
                select dep.id as department_id, imp.* from dym_improvement imp
                left join improvement_departments_rel idr on idr.improvement_id = imp.id
                left join hr_department dep on dep.id = idr.department_id
                where """+where_tahun+"""
                and """+where_state+"""
                and """+where_level+"""
                and """+where_jenis_improvement+"""
                )i on i.department_id = d.id
            where 1=1 
            --and d.loc is not null 
            and d.name != 'CEO'
            --and d.loc not ilike 'Area : %'
            and """+where_department+"""

            group by par.name,d.name
            order by par.name,d.name
        """
        reports = [report_ss]

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
                        'parent': str(x['parent']) if x['parent'] != None else '',
                        'department': str(x['department']) if x['department'] != None else '',
                        'januari': int(x['januari']) if x['januari'] != None else 0,
                        'nqi_jan': float(x['nqi_jan']) if x['nqi_jan'] != None else 0,
                        'februari': int(x['februari']) if x['februari'] != None else 0,
                        'nqi_feb': float(x['nqi_feb']) if x['nqi_feb'] != None else 0,
                        'maret': int(x['maret']) if x['maret'] != None else 0,
                        'nqi_mar': float(x['nqi_mar']) if x['nqi_mar'] != None else 0,
                        'april': int(x['april']) if x['april'] != None else 0,
                        'nqi_apr': float(x['nqi_apr']) if x['nqi_apr'] != None else 0,
                        'mei': int(x['mei']) if x['mei'] != None else 0,
                        'nqi_mei': float(x['nqi_mei']) if x['nqi_mei'] != None else 0,
                        'juni': int(x['juni']) if x['juni'] != None else 0,
                        'nqi_jun': float(x['nqi_jun']) if x['nqi_jun'] != None else 0,
                        'juli': int(x['juli']) if x['juli'] != None else 0,
                        'nqi_jul': float(x['nqi_jul']) if x['nqi_jul'] != None else 0,
                        'agustus': int(x['agustus']) if x['agustus'] != None else 0,
                        'nqi_ags': float(x['nqi_ags']) if x['nqi_ags'] != None else 0,
                        'september': int(x['september']) if x['september'] != None else 0,
                        'nqi_sep': float(x['nqi_sep']) if x['nqi_sep'] != None else 0,
                        'oktober': int(x['oktober']) if x['oktober'] != None else 0,
                        'nqi_okt': float(x['nqi_okt']) if x['nqi_okt'] != None else 0,
                        'november': int(x['november']) if x['november'] != None else 0,
                        'nqi_nov': float(x['nqi_nov']) if x['nqi_nov'] != None else 0,
                        'desember': int(x['desember']) if x['desember'] != None else 0,
                        'nqi_des': float(x['nqi_des']) if x['nqi_des'] != None else 0                        
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
        state = data.get('state')
        tahun = data.get('tahun')
        jenis_improvement = data.get('jenis_improvement')
        level = data.get('level')

        datas = self.get_data(state, tahun, department_ids, jenis_improvement, level)

        row = 0
        col = 0

        sheet = workbook.add_worksheet("Report QCC, QCP, PPS, 5R, Safety Improvement tahunan")
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
        sheet.set_column('D:AA', 15)


        sheet.set_row(row + 3, 30)

        sheet.write(row, 0, 'Report QCC, QCP, PPS, 5R, Safety Improvement Berdasarkan Tanggal Didaftarkan', bold)
        sheet.write(row + 1, 0, 'Tahun : %s' % (tahun))
        sheet.write(row + 3, 0, 'No.', header_format)
        sheet.write(row + 3, 1, 'Parent', header_format)
        sheet.write(row + 3, 2, 'Department', header_format)
        sheet.write(row + 3, 3, 'Count Jan', header_format)
        sheet.write(row + 3, 4, 'NQI Jan', header_format)
        sheet.write(row + 3, 5, 'Count Feb', header_format)
        sheet.write(row + 3, 6, 'NQI Feb', header_format)
        sheet.write(row + 3, 7, 'Count Mar', header_format)
        sheet.write(row + 3, 8, 'NQI Mar', header_format)
        sheet.write(row + 3, 9, 'Count Apr', header_format)
        sheet.write(row + 3, 10, 'NQI Apr', header_format)
        sheet.write(row + 3, 11, 'Count Mei', header_format)
        sheet.write(row + 3, 12, 'NQI Mei', header_format)
        sheet.write(row + 3, 13, 'Count Jun', header_format)
        sheet.write(row + 3, 14, 'NQI Jun', header_format)
        sheet.write(row + 3, 15, 'Count Jul', header_format)
        sheet.write(row + 3, 16, 'NQI Jul', header_format)
        sheet.write(row + 3, 17, 'Count Ags', header_format)
        sheet.write(row + 3, 18, 'NQI Ags', header_format)
        sheet.write(row + 3, 19, 'Count Sep', header_format)
        sheet.write(row + 3, 20, 'NQI Sep', header_format)
        sheet.write(row + 3, 21, 'Count Okt', header_format)
        sheet.write(row + 3, 22, 'NQI Okt', header_format)
        sheet.write(row + 3, 23, 'Count Nov', header_format)
        sheet.write(row + 3, 24, 'NQI Nov', header_format)
        sheet.write(row + 3, 25, 'Count Des', header_format)
        sheet.write(row + 3, 26, 'NQI Des', header_format)
        sheet.write(row + 3, 27, 'Total SS', header_format)
        sheet.write(row + 3, 28, 'Total NQI', header_format)
        
        row += 4
        no = 1
        total_ss = 0
        total_nqi = 0
        if datas:
            for x in datas:
                # _logger.info('OBJ '+str(x))

                sheet.write(row, 0, no, center_format)
                sheet.write(row, 1, x['parent'])
                sheet.write(row, 2, x['department'])
                sheet.write(row, 3, x['januari'],center_format)
                sheet.write(row, 4, round(x['nqi_jan'],2), right_format)
                sheet.write(row, 5, x['februari'],center_format)
                sheet.write(row, 6, round(x['nqi_feb'],2), right_format)
                sheet.write(row, 7, x['maret'],center_format)
                sheet.write(row, 8, round(x['nqi_mar'],2), right_format)
                sheet.write(row, 9, x['april'],center_format)
                sheet.write(row, 10, round(x['nqi_apr'],2), right_format)
                sheet.write(row, 11, x['mei'],center_format)
                sheet.write(row, 12, round(x['nqi_mei'],2), right_format)
                sheet.write(row, 13, x['juni'],center_format)
                sheet.write(row, 14, round(x['nqi_jun'],2), right_format)
                sheet.write(row, 15, x['juli'],center_format)
                sheet.write(row, 16, round(x['nqi_jul'],2), right_format)
                sheet.write(row, 17, x['agustus'],center_format)
                sheet.write(row, 18, round(x['nqi_ags'],2), right_format)
                sheet.write(row, 19, x['september'],center_format)
                sheet.write(row, 20, round(x['nqi_sep'],2), right_format)
                sheet.write(row, 21, x['oktober'],center_format)
                sheet.write(row, 22, round(x['nqi_okt'],2), right_format)
                sheet.write(row, 23, x['november'],center_format)
                sheet.write(row, 24, round(x['nqi_nov'],2), right_format)
                sheet.write(row, 25, x['desember'],center_format)
                sheet.write(row, 26, round(x['nqi_des'],2), right_format)
                total_ss = int(x['januari']) + int(x['februari']) + int(x['maret']) + int(x['april']) + int(x['mei']) + int(x['juni']) + int(x['juli']) + int(x['agustus']) + int(x['september']) + int(x['oktober']) + int(x['november']) + int(x['desember']) 
                total_nqi = int(x['nqi_jan']) + int(x['nqi_feb']) + int(x['nqi_mar']) + int(x['nqi_apr']) + int(x['nqi_mei']) + int(x['nqi_jun']) + int(x['nqi_jul']) + int(x['nqi_ags']) + int(x['nqi_sep']) + int(x['nqi_okt']) + int(x['nqi_nov']) + int(x['nqi_des'])
                sheet.write(row, 27, total_ss,center_format)
                sheet.write(row, 28, total_nqi,right_format)
            
                row += 1
                no += 1

            sheet.write(row, 3,  '=SUM(D5:D'+str(row)+')', footer_format)
            sheet.write(row, 4,  '=SUM(E5:E'+str(row)+')', footer_format)
            sheet.write(row, 5,  '=SUM(F5:F'+str(row)+')', footer_format)
            sheet.write(row, 6,  '=SUM(G5:G'+str(row)+')', footer_format)
            sheet.write(row, 7,  '=SUM(H5:H'+str(row)+')', footer_format)
            sheet.write(row, 8,  '=SUM(I5:I'+str(row)+')', footer_format)
            sheet.write(row, 9, '=SUM(J5:J'+str(row)+')', footer_format)
            sheet.write(row, 10, '=SUM(K5:K'+str(row)+')', footer_format)
            sheet.write(row, 11, '=SUM(L5:L'+str(row)+')', footer_format)
            sheet.write(row, 12, '=SUM(M5:M'+str(row)+')', footer_format)
            sheet.write(row, 13, '=SUM(N5:N'+str(row)+')', footer_format)
            sheet.write(row, 14, '=SUM(O5:O'+str(row)+')', footer_format)
            sheet.write(row, 15, '=SUM(P5:P'+str(row)+')', footer_format)
            sheet.write(row, 16, '=SUM(Q5:Q'+str(row)+')', footer_format)
            sheet.write(row, 17, '=SUM(R5:R'+str(row)+')', footer_format)
            sheet.write(row, 18, '=SUM(S5:S'+str(row)+')', footer_format)
            sheet.write(row, 19, '=SUM(T5:T'+str(row)+')', footer_format)
            sheet.write(row, 20, '=SUM(U5:U'+str(row)+')', footer_format)
            sheet.write(row, 21, '=SUM(V5:V'+str(row)+')', footer_format)
            sheet.write(row, 22, '=SUM(W5:W'+str(row)+')', footer_format)
            sheet.write(row, 23, '=SUM(X5:X'+str(row)+')', footer_format)
            sheet.write(row, 24, '=SUM(Y5:Y'+str(row)+')', footer_format)
            sheet.write(row, 25, '=SUM(Z5:Z'+str(row)+')', footer_format)
            sheet.write(row, 26, '=SUM(AA5:AA'+str(row)+')', footer_format)
            sheet.write(row, 27, '=SUM(AB5:AB'+str(row)+')', footer_format)
            sheet.write(row, 28,  '=SUM(AC5:AC'+str(row)+')', footer_format)

            

            sheet.write(row + 1, 0, None)
            sheet.write(row + 2, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))
        else:
            sheet.write(row, 0, 'No Data Found')
            sheet.write(row + 3, 0,
                        time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(self.env['res.users'].browse(self._uid).name))