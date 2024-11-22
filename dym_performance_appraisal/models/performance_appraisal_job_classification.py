import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class performance_appraisal_job_classification(models.Model):
    _name = 'performance.appraisal.job.classification'
    _description = 'Form Job Classification'

    def _get_form_id_domain(self):
        domain = [(1,'=',1)]
        form_a = self.env.ref('dym_performance_appraisal.model_dym_performance_appraisal_form_a')
        form_b = self.env.ref('dym_performance_appraisal.model_dym_performance_appraisal_form_b')
        if form_a and form_b:
            domain = [('id','in',[form_a.id,form_b.id])]
        return domain

    form_id = fields.Many2one('ir.model', string='Form', domain=_get_form_id_domain, required=True, ondelete="cascade")
    job_ids = fields.Many2many('hr.job', string='Job Selection')


    # @api.constrains('form_id','job_ids','job_ids.ids')
    # def _constrains_form_job(self):
    #     for record in self:
    #         # check if job are duplicated
    #         if record.form_id and record.job_ids:
    #             job_classifications = record._name.search([
    #                 ('id','!=',record.id),
    #                 ('job_ids.id','in',record.job_ids.ids)
    #             ])
    #             if job_classifications:
    #                 pass
    

    # generate employee every year
    def cron_generate_performance_emp_every_year(self):
        # FORM A
        form_a_classification = self.env.ref('dym_performance_appraisal.form_a_job_classification')
        form_a_appraisal = self.env.ref('dym_performance_appraisal.model_dym_performance_appraisal_form_a')

        if form_a_classification and form_a_appraisal:
            employees = self.env['hr.employee'].search([
                ('job_id','in',form_a_classification.job_ids.ids)
            ])
            for emp in employees:
                self.env[form_a_appraisal.model].create({
                    'employee_id': emp.id,
                    'job_id': emp.job_id.id,
                    'department_id': emp.department_id.id,
                    'atasan_1': emp.parent_id.id,
                    'atasan_2': emp.parent_id.parent_id.id,
                })
        
        # FORM B
        form_b_classification = self.env.ref('dym_performance_appraisal.form_b_job_classification')
        form_b_appraisal = self.env.ref('dym_performance_appraisal.model_dym_performance_appraisal_form_b')

        if form_b_classification and form_b_appraisal:
            employees = self.env['hr.employee'].search([
                ('job_id','in',form_b_classification.job_ids.ids)
            ])
            for emp in employees:
                self.env[form_b_appraisal.model].create({
                    'employee_id': emp.id,
                    'job_id': emp.job_id.id,
                    'department_id': emp.department_id.id,
                    'atasan_1': emp.parent_id.id,
                    'atasan_2': emp.parent_id.parent_id.id,
                })
        
