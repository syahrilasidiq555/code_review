from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

class hr_work_location(models.Model):
    _inherit = 'hr.work.location'
    
    latitude = fields.Char('Latitude')
    longitude = fields.Char('Longitude')

    is_wonogiri_area = fields.Boolean('Is Wonogiri Area')