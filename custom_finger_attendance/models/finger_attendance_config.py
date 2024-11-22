import time
from datetime import datetime, timedelta

import json
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

import pyodbc

# from odoo.osv import osv

class finger_attendance_config(models.Model):
    _name = 'finger.attendance.config'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Finger Attendance'
    
    name = fields.Char('Name', required=True, tracking=True)
    destination = fields.Char('Destination', required=True, tracking=True)
    absen_loc = fields.Selection([
        ('bandung', 'Bandung'),
        ('wono', 'Wonogiri'),
    ], string='Absen Location', default="bandung", required=True)
    file_method = fields.Selection([
        ('exact', 'Exact Destination'),
        ('copy', 'Copy to Location'),
    ], string='DB File Method', required=True, default="exact", tracking=True)
    copy_destination = fields.Char('Destination', tracking=True)

    driver = fields.Char('Driver', required=True, tracking=True)
    username = fields.Char('Username', required=True, tracking=True)
    password = fields.Char('Password')

    last_generated = fields.Datetime(string='Last Attendance Generated')

    active = fields.Boolean('Active', default=True)


    def action_copy_destination(self):
        for record in self:
            if record.file_method and record.file_method == 'copy':
                import shutil
                # Specify the path of the file you want to copy
                file_to_copy = record.destination

                # Specify the path of the destination directory you want to copy to
                destination_directory = record.copy_destination

                # Use the shutil.copy() method to copy the file to the destination directory
                shutil.copy(file_to_copy, destination_directory)

    def action_test_connection(self):
        for record in self:
            record.action_copy_destination()
            # set up some constants
            MDB = record.destination if record.file_method == 'exact' else record.copy_destination
            # DRV = '{Microsoft Access Driver (*.mdb)}'
            # UID = 'admin'
            # PWD = 'ithITtECH'
            DRV = record.driver
            UID = record.username
            PWD = record.password
            try:
                con = pyodbc.connect('DRIVER={};DBQ={};UID={};PWD={}'.format(DRV,MDB,UID,PWD))
                raise UserError("Successfully Connected!")
            except Exception as e:
                raise UserError(e)


    def action_get_attendance(self, date=False, shift3=False):
        for record in self:
            record.action_copy_destination()

            date_now = datetime.now() + timedelta(hours=7)

            # set up some constants
            MDB = record.destination if record.file_method == 'exact' else record.copy_destination
            # DRV = '{Microsoft Access Driver (*.mdb)}'
            # UID = 'admin'
            # PWD = 'ithITtECH'
            DRV = record.driver
            UID = record.username
            PWD = record.password
            con = pyodbc.connect('DRIVER={};DBQ={};UID={};PWD={}'.format(DRV,MDB,UID,PWD))
            cur = con.cursor()

            date_input = date_now if not date else date
            date_next = date_input + timedelta(days=1)

            # run a query and get the results 
            if shift3:
                # get shift3 employee
                list_fingerprintID = None
                shift3_employee = self.env['hr.employee'].sudo().search([
                    ('resource_calendar_id.is_shift_3','=',shift3),
                    ('fingerprint_id','>',0),
                ])
                if shift3_employee:
                    list_fingerprintID = tuple(int(x.fingerprint_id) for x in shift3_employee)
                    list_fingerprintID2 = tuple(str(x.fingerprint_id) for x in shift3_employee)
                else:
                    raise UserError("No Attendance Result!")
                
                if record.absen_loc == 'bandung':
                    SQL = f'''
                        SELECT
                            e.FingerPrintID, log_checkin.checkin as checkin, log_checkout.checkout as checkout
                        FROM (Employee e
                        left join (
                            SELECT
                                ci.FingerPrintID as FingerPrintID, max(ci.DateTime) as checkin
                            FROM PersonalLog ci
                            WHERE ci.FingerPrintID in {str(list_fingerprintID)}
                                and Year([ci.DateLog]) = {date_input.year} 
                                and Month([ci.DateLog]) = {date_input.month} 
                                and Day([ci.DateLog]) = {date_input.day}
                            group by FingerPrintID
                        ) log_checkin ON e.FingerPrintID = log_checkin.FingerPrintID)
                        left join (
                            SELECT
                                co.FingerPrintID as FingerPrintID, min(co.DateTime) as checkout
                            FROM PersonalLog co
                            WHERE co.FingerPrintID in {str(list_fingerprintID)}
                                and Year([co.DateLog]) = {date_next.year} 
                                and Month([co.DateLog]) = {date_next.month} 
                                and Day([co.DateLog]) = {date_next.day}
                            group by FingerPrintID
                        ) log_checkout ON e.FingerPrintID = log_checkout.FingerPrintID

                        WHERE e.FingerPrintID in {str(list_fingerprintID)}
                    '''
                elif record.absen_loc == 'wono':
                    # SQL = f'''
                    #     SELECT
                    #         e.USERID as FingerPrintID, log_checkin.checkin as checkin, log_checkout.checkout as checkout
                    #     FROM (USERINFO e
                    #     left join (
                    #         SELECT
                    #             ci.USERID as USERID, max(ci.CHECKTIME) as checkin
                    #         FROM CHECKINOUT ci
                    #         WHERE ci.USERID in {str(list_fingerprintID)}
                    #             and Year([ci.CHECKTIME]) = {date_input.year} 
                    #             and Month([ci.CHECKTIME]) = {date_input.month} 
                    #             and Day([ci.CHECKTIME]) = {date_input.day}
                    #         group by USERID
                    #     ) log_checkin ON e.USERID = log_checkin.USERID)
                    #     left join (
                    #         SELECT
                    #             co.USERID as USERID, min(co.CHECKTIME) as checkout
                    #         FROM CHECKINOUT co
                    #         WHERE co.USERID in {str(list_fingerprintID)}
                    #             and Year([co.CHECKTIME]) = {date_next.year} 
                    #             and Month([co.CHECKTIME]) = {date_next.month} 
                    #             and Day([co.CHECKTIME]) = {date_next.day}
                    #         group by USERID
                    #     ) log_checkout ON e.USERID = log_checkout.USERID

                    #     WHERE e.USERID in {str(list_fingerprintID)}
                    # '''
                    SQL = f'''
                        SELECT
                            e.Badgenumber as FingerPrintID, log_checkin.checkin as checkin, log_checkout.checkout as checkout
                        FROM (USERINFO e
                        left join (
                            SELECT
                                ui.Badgenumber as Badgenumber, max(ci.CHECKTIME) as checkin
                            FROM CHECKINOUT ci
                            left join USERINFO ui on ui.USERID = ci.USERID
                            WHERE ui.Badgenumber in {str(list_fingerprintID2)}
                                and Year([ci.CHECKTIME]) = {date_input.year} 
                                and Month([ci.CHECKTIME]) = {date_input.month} 
                                and Day([ci.CHECKTIME]) = {date_input.day}
                            group by ui.Badgenumber

                        ) log_checkin ON e.Badgenumber = log_checkin.Badgenumber)
                        left join (
                            SELECT
                                ui.Badgenumber as Badgenumber, min(co.CHECKTIME) as checkout
                            FROM CHECKINOUT co
                            left join USERINFO ui on ui.USERID = co.USERID
                            WHERE ui.Badgenumber in {str(list_fingerprintID2)}
                                and Year([co.CHECKTIME]) = {date_next.year} 
                                and Month([co.CHECKTIME]) = {date_next.month} 
                                and Day([co.CHECKTIME]) = {date_next.day}
                            group by ui.Badgenumber

                        ) log_checkout ON e.Badgenumber = log_checkout.Badgenumber

                        WHERE e.Badgenumber in {str(list_fingerprintID2)}
                    '''
            else:
                if record.absen_loc == 'bandung':
                    SQL = f'''
                        SELECT
                        log.FingerPrintID, min(log.DateTime) as checkin, max(log.DateTime) as checkout
                        FROM PersonalLog log
                        WHERE Year([DateLog]) = {date_input.year} and Month([DateLog]) = {date_input.month} and Day([DateLog]) = {date_input.day}
                        group by FingerPrintID
                    '''
                elif record.absen_loc == 'wono':
                    # SQL = f'''
                    #     SELECT
                    #     log.USERID as FingerPrintID, min(log.CHECKTIME) as checkin, max(log.CHECKTIME) as checkout
                    #     FROM CHECKINOUT log
                    #     WHERE 
                    #     Year([CHECKTIME]) = {date_input.year} 
                    #     and Month([CHECKTIME]) = {date_input.month} 
                    #     and Day([CHECKTIME]) = {date_input.day}
                    #     group by USERID
                    # '''
                    SQL = f'''
                        SELECT
                            ui.Badgenumber as FingerPrintID, min(log.CHECKTIME) as checkin, max(log.CHECKTIME) as checkout
                        FROM CHECKINOUT log
                        left join USERINFO ui on ui.USERID = log.USERID
                        WHERE 
                        Year([CHECKTIME]) = {date_input.year}
                        and Month([CHECKTIME]) = {date_input.month}
                        and Day([CHECKTIME]) = {date_input.day}
                        group by ui.Badgenumber 
                    '''
            # raise UserError(SQL)
            
            cur.execute(SQL)
            # tables = list(cur.tables())
            columns = [column[0] for column in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            cur.close()
            con.close()
            # raise UserError(str(results))
            if results:
                record.generate_attendance(results, shift3)
                if not date:
                    record.last_generated = datetime.now()
            else:
                raise UserError("No Attendance Result!")

    def generate_attendance(self, results, shift3=False):
        for result in results:
            employee = self.env['hr.employee'].search([
                ('fingerprint_id','=',str(result['FingerPrintID'])),
                ('resource_calendar_id.is_shift_3','=',shift3),
            ], limit=1)
            if employee:
                try:
                    # validate if attendance already exist:
                    exist_attendance = self.env['hr.attendance'].sudo().search([
                        ('employee_id','=', employee[0].id),
                        ('check_out','>=', result['checkin'] - timedelta(hours=7)),
                        ('check_in','<=', result['checkout'] - timedelta(hours=7)),
                    ])
                    if not exist_attendance:
                        attendance = self.env['hr.attendance'].sudo().create({
                            'employee_id':employee[0].id,
                            'check_in': result['checkin'] - timedelta(hours=7),
                            'check_out': result['checkout'] - timedelta(hours=7),
                            'attendance_from':'fingerprint'
                        })
                    elif exist_attendance and exist_attendance.worked_hours < 5:
                        exist_attendance[0].sudo().write({
                            # 'employee_id':employee[0].id,
                            'check_in': result['checkin'] - timedelta(hours=7),
                            'check_out': result['checkout'] - timedelta(hours=7),
                            'attendance_from':'fingerprint'
                        })
                except Exception as e:
                    print(f"gagal absen\n\nFingerprintID: {result['FingerPrintID']}\nMessage:{e}")

    def action_read_text_file(self):
        for record in self:
            file = open(record.destination, "r")
            content = file.read()
            raise UserError(content)
        


    # button action
    def action_generate_attendance_by_date(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_finger_config_id':record.id,
                    'default_attendance_date':(datetime.now() + timedelta(hours=7)).date(),
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Generate Attendance',
                    'res_model':'generate.attendance.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_finger_attendance.generate_attendance_wizard_form_view').id,
                    'view_mode':'form',
                    'target':'new',
                    'context':context
                    }



    # SCHEDULED ACTION
    def cron_generate_finger_attendance(self,date=False,shift3=False):
        date_now = datetime.now() + timedelta(hours=7)
        
        date_input = date_now if not date else date
        
        finger_configs = self.env['finger.attendance.config'].sudo().search([])
        for config in finger_configs:
            config.action_get_attendance(date=date_input,shift3=shift3)
            config.last_generated = date_input