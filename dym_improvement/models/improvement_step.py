import time
from datetime import datetime

# import json
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
from odoo import SUPERUSER_ID

from odoo.osv import osv
import logging 


class improvement_step(models.Model):
    _name = 'improvement.step'
    _description = 'Improvement Step'
    _order = 'sequence, id'

    name = fields.Char(string='Step', required=True)
    sequence = fields.Integer(default=1)
    description = fields.Text(translate=True)
    jenis_improvement = fields.Selection(
        [('qcc','QCC'),
        ('qcp','QCP'),
        ('qcl','QCL'),
        ('pps','PPS'),
        ('fiver','5R'),
        ('safety_improvement','Safety Improvement')],
        string='Jenis Improvement',
        required=True)
    active = fields.Boolean(string='Active', default=True)
    
    def unlink(self):
        for record in self:
            raise ValidationError(_('You cannot delete this step, please use archieve instead of unlink'))
            res = super(improvement_step,self).unlink()
            return res
    
    def set_unactive(self):
        for record in self:
            record.active = False
    
    def set_active(self):
        for record in self:
            record.active = True
    