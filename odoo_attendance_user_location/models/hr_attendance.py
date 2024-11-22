# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class HrAttendance(models.Model):
    """Inherits HR Attendance model to add the checkin and checkout fields"""
    _inherit = 'hr.attendance'

    checkin_address = fields.Char(string='Check In Address', store=True,
                                help="Check in address of the User")
    checkout_address = fields.Char(string='Check Out Address', store=True,
                                help="Check out address of the User")
    checkin_latitude = fields.Char(string='Check In Latitude', store=True,
                                help="Check in latitude of the User")
    checkout_latitude = fields.Char(string='Check Out Latitude', store=True,
                                    help="Check out latitude of the User")
    checkin_longitude = fields.Char(string='Check In Longitude', store=True,
                                    help="Check in longitude of the User")
    checkout_longitude = fields.Char(string='Check Out Longitude', store=True,
                                    help="Check out longitude of the User")
    checkin_location = fields.Char(string='Check In Location Url', store=True,
                                help="Check in location Url of the User")
    checkout_location = fields.Char(string='Check Out Location Url',
                                    store=True,
                                    help="Check out location Url of the User")

    image_checkin = fields.Binary(string='Check In Image', attachment=True, store=True)
    image_checkin_filename = fields.Char(string='Filename Check In Image')
    image_checkin_view = fields.Binary(related="image_checkin")
