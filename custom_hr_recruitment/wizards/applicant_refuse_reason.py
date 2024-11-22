# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class applicant_get_refuse_reason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'

    def action_refuse_reason_apply(self):
        res = super(applicant_get_refuse_reason,self).action_refuse_reason_apply()
        self.applicant_ids.write({
            'stage_id': self.env.ref('custom_hr_recruitment.stage_job_refused').id,
            'active': True
        })
        return res