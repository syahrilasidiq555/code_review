# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import timedelta

from math import sin, cos, sqrt, atan2, radians

# Approximate radius of earth in km
R = 6373.0


def calculate_distance(latitude1, longitude1, latitude2, longitude2):
    def_lat = radians(latitude1)
    def_lon = radians(longitude1)
    lat2 = radians(latitude2)
    lon2 = radians(longitude2)

    dlon = lon2 - def_lon
    dlat = lat2 - def_lat

    a = sin(dlat / 2)**2 + cos(def_lat) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = (R * c) * 1000 

    return distance

class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Hours')
    waktu_terlambat = fields.Float(compute="_compute_terlambat", string='Waktu Terlambat', store=True)
    terlambat = fields.Boolean(compute="_compute_terlambat", string='Terlambat', store=True)
    attendance_from = fields.Selection([
        ('fingerprint', 'Fingerprint Machine'),
        ('odoo','ODOO')
    ], string='Attendance From', required=True, default='odoo')

    form_lupa_absen_id = fields.Many2one('form.lupa.absen', string='Form Lupa Absen')
    is_from_lupa_absen = fields.Boolean(compute='_compute_is_from_lupa_absen', string='Absen dari Form Lupa Absen')
    @api.depends('form_lupa_absen_id')
    def _compute_is_from_lupa_absen(self):
        for record in self:
            record.is_from_lupa_absen = False
            if record.form_lupa_absen_id:
                record.is_from_lupa_absen = True

    work_location_id = fields.Many2one(related="employee_id.work_location_id")
    
    distance_checkin = fields.Float(compute='_compute_distance_checkin', string='Distance Checkin')
    distance_checkin_string = fields.Char(compute='_compute_distance_checkin', string='Distance Checkin')
    
    @api.depends('employee_id','employee_id.work_location_id','check_in','write_date')
    def _compute_distance_checkin(self):
        for record in self:
            distance_checkin = 0
            distance_checkin_string = ''

            if record.check_in and record.employee_id and record.employee_id.work_location_id and record.checkin_latitude and record.checkin_longitude:
                if record.employee_id.work_location_id.latitude and record.employee_id.work_location_id.longitude:
                    distance_checkin = calculate_distance(
                        latitude1 = float(record.employee_id.work_location_id.latitude),
                        longitude1 = float(record.employee_id.work_location_id.longitude),
                        latitude2 = float(record.checkin_latitude),
                        longitude2 = float(record.checkin_longitude),
                    )
                    if distance_checkin:
                        distance_checkin_string = f"{round(distance_checkin,2)} m from {record.employee_id.work_location_id.name}"

            record.distance_checkin = distance_checkin
            record.distance_checkin_string = distance_checkin_string
    
    distance_checkout = fields.Float(compute='_compute_distance_checkout', string='Distance checkout')
    distance_checkout_string = fields.Char(compute='_compute_distance_checkout', string='Distance checkout')
    
    @api.depends('employee_id','employee_id.work_location_id','check_out','write_date')
    def _compute_distance_checkout(self):
        for record in self:
            distance_checkout = 0
            distance_checkout_string = ''

            if record.check_out and record.employee_id and record.employee_id.work_location_id and record.checkout_latitude and record.checkout_longitude:
                if record.employee_id.work_location_id.latitude and record.employee_id.work_location_id.longitude:
                    distance_checkout = calculate_distance(
                        latitude1 = float(record.employee_id.work_location_id.latitude),
                        longitude1 = float(record.employee_id.work_location_id.longitude),
                        latitude2 = float(record.checkout_latitude),
                        longitude2 = float(record.checkout_longitude),
                    )
                    if distance_checkout:
                        distance_checkout_string = f"{round(distance_checkout,2)} m from {record.employee_id.work_location_id.name}"

            record.distance_checkout = distance_checkout
            record.distance_checkout_string = distance_checkout_string

    # @api.depends('check_in','employee_id')
    # def _compute_terlambat(self):
    #     for record in self:
    #         record.terlambat = False
    #         if record.check_in and record.employee_id:
    #             check_in = record.check_in + timedelta(hours=7)
    #             checkin_hour = round(check_in.hour + (check_in.minute/60),2)
    #             checkin_day = check_in.weekday()

    #             # ----cek data working time hari ini
    #             query_cek_terlambat = """
    #                 with c as (
    #                     select e.id, e.resource_calendar_id, work_time.id rc_id, work_time.rcl_id as rcl_id
    #                     from hr_employee e
    #                     left join (
    #                         select rc.id as id, 
    #                             rcl.id as rcl_id
    #                         from resource_calendar rc
    #                         left join resource_calendar_attendance rcl on rcl.calendar_id = rc.id
    #                         where rcl.dayofweek = '"""+str(checkin_day)+"""' 
    #                         --and rcl.hour_from <= """+str(checkin_hour)+""" and rcl.hour_to >= """+str(checkin_hour)+"""
    #                         group by rc.id, rcl.id
    #                     ) work_time on work_time.id = e.resource_calendar_id
    #                     where e.id = """+str(record.employee_id.id)+"""
    #                     and work_time.id is not null)
                    
    #                 select * from resource_calendar_attendance
    #                 where calendar_id in (select rc_id from c)
    #                 and dayofweek = '"""+str(checkin_day)+"""'
    #                 order by sequence asc
    #             """
    #             self._cr.execute(query_cek_terlambat)
    #             # raise osv.except_osv(_('Warning!'),_('data : '+str(query)))
    #             all_lines = self._cr.dictfetchall()
    #             waktu_terlambat = 0
    #             terlambat = False
    #             if all_lines:
    #                 jam_masuk = all_lines[0]['hour_from']
    #                 waktu_terlambat = checkin_hour - jam_masuk if (checkin_hour - jam_masuk) > 0 else 0 
    #                 terlambat = True if waktu_terlambat > 0 else False

    #             record.waktu_terlambat = waktu_terlambat
    #             record.terlambat = terlambat


    @api.depends('check_in','employee_id', 'resource_calendar_id')
    def _compute_terlambat(self):
        for record in self:
            record.waktu_terlambat = 0
            record.terlambat = False
            if record.check_in and record.employee_id and record.resource_calendar_id:
                check_in = record.check_in + timedelta(hours=7)
                checkin_hour = round(check_in.hour + (check_in.minute/60),2)
                checkin_day = check_in.weekday()

                # get data terlambat
                # waktu_terlambat = 0
                # terlambat = False
                work_attendance = record.resource_calendar_id.attendance_ids.filtered(
                    lambda x: x.dayofweek == str(checkin_day)
                ).sorted(key=lambda r: r.sequence)
                if work_attendance:
                    if record.resource_calendar_id.is_shift_3:
                        jam_masuk = work_attendance[-1].hour_from
                        record.waktu_terlambat = checkin_hour - jam_masuk if (checkin_hour - jam_masuk) > 0 else 0 
                        record.terlambat = True if record.waktu_terlambat > 0 else False
                    else:
                        jam_masuk = work_attendance[0].hour_from
                        record.waktu_terlambat = checkin_hour - jam_masuk if (checkin_hour - jam_masuk) > 0 else 0 
                        record.terlambat = True if record.waktu_terlambat > 0 else False


    # VALIDASI EMPLOYEE YG ABSEN FINGERPRINT ONLY TIDAK BISA ABSEN LEWAT ATTENDANCE ODOO
    @api.constrains('employee_id','employee_id.attendance_mode')
    def _constrains_attendance_mode(self):
        for record in self:
            if record.employee_id and record.employee_id.attendance_mode not in ['geo_selfie','finger_geo_selfie']:
                if record.attendance_from != 'fingerprint':
                    raise ValidationError("Employee hanya bisa absen melalui fingerprint, silahkan set 'Attendance Mode' di master employee!")
                

    @api.model
    def create(self, vals):
        if vals.get('employee_id'):
            emp = self.env['hr.employee'].sudo().browse(vals.get('employee_id'))
            if emp:
                vals['resource_calendar_id'] = emp.resource_calendar_id.id
        result = super(hr_attendance, self).create(vals)
        return result