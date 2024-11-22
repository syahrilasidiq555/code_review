# from attr import field
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta

class crm_lead(models.Model):
    _inherit = "crm.lead"

    type_business = fields.Selection([
        ('new', 'New Business'),
        ('existing', 'Existing Business'),
    ], string='Business Type', required=True, default='new')

    campaign_id = fields.Many2one(required=True, ondelete="restrict")
    medium_id = fields.Many2one(required=True, ondelete="restrict")
    source_id = fields.Many2one(required=True, ondelete="restrict")

    last_stage_moved = fields.Datetime(string='Last Stage Moved')

    is_lost = fields.Boolean(related="stage_id.is_lost", string='Is Lost?')

    day_close_today = fields.Integer(compute='_compute_day_close_today', string='Day to close until today')

    # @api.depends('create_date')
    def _compute_day_close_today(self):
        for record in self:
            date_create = fields.Datetime.from_string(record.create_date)
            date_close = datetime.now()
            record.date_deadline = date_close
            record.day_close_today = abs((date_close - date_create).days)

    @api.onchange('stage_id')
    def _onchange_last_stage_moved(self):
        for record in self:
            if record.stage_id and record.stage_id.id and record._origin.stage_id.id:
                record.last_stage_moved = datetime.now()
    
    # override set lost function
    def action_set_lost(self, **additional_values):
        res = super(crm_lead, self).action_set_lost(**additional_values)
        for record in self:
            vals = {
                'active':True,
            }
            stage_lost_id = self.env['crm.stage'].search([('is_lost','=',True)])
            if stage_lost_id:
                vals['stage_id'] = stage_lost_id[0].id
            record.sudo().write(vals)
        return res
    
    # SCHEDULE ACTION
    # reminder salesperson dan team leader jika stage tidak berubah selama 1 bulan 
    def cron_reminder_not_moved_pipeline(self,date=datetime.now()):
        date_to_reminder = date - relativedelta(months=1)
        pipelines = self.env['crm.lead'].search([
            ('type','=','opportunity'),
            ('last_stage_moved','>=',date_to_reminder.replace(hour=0,minute=0,second=0)),
            ('last_stage_moved','<=',date_to_reminder.replace(hour=23,minute=59,second=59)),
            ('stage_id.is_won','=',False),
            ('stage_id.is_lost','=',False),
        ])
        for pipeline in pipelines:
            # create schedule activity 
            # reminder to salesperson
            if pipeline.user_id:
                self.env['mail.activity'].create({
                    'summary': f'Reminder Opportunity',
                    'note': f'Dear salesperson, this opportunity is still not move since 1 month before. Please update this opportunity stage or set it to Lost',
                    'date_deadline': datetime.now(),
                    'user_id': pipeline.user_id.id,
                    'res_id': pipeline.id,
                    'res_model_id': self.env.ref('crm.model_crm_lead').id,
                    'activity_type_id': self.env.ref('project_todo.mail_activity_data_reminder').id
                })

            # reminder to manager
            if pipeline.team_id and pipeline.team_id.user_id:
                self.env['mail.activity'].create({
                    'summary': f'Reminder Opportunity',
                    'note': f'Dear Leader of {pipeline.team_id.name}, this opportunity is still not move since 1 month before. Please update this opportunity stage or set it to Lost',
                    'date_deadline': datetime.now(),
                    'user_id': pipeline.team_id.user_id.id,
                    'res_id': pipeline.id,
                    'res_model_id': self.env.ref('crm.model_crm_lead').id,
                    'activity_type_id': self.env.ref('project_todo.mail_activity_data_reminder').id
                })

    # cron reminder manager rata2 date to win lebih besar
    def cron_reminder_not_moved_pipeline(self,date=datetime.now()):
        # get average days to close
        average_day_close = 0
        query = '''
            select avg(lead.day_close) as avg
            from crm_lead lead
            left join crm_stage stg on stg.id = lead.stage_id
            where stg.is_won = True
        '''
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        average_day_close = datas[0]['avg'] if datas else average_day_close

        pipelines = self.env['crm.lead'].search([
            ('type','=','opportunity'),
            ('stage_id.is_won','=',False),
            ('stage_id.is_lost','=',False),
            ('day_close_today','>',average_day_close),
        ])
        for pipeline in pipelines:
            # create schedule activity 

            # reminder to manager
            if pipeline.team_id and pipeline.team_id.user_id:
                self.env['mail.activity'].create({
                    'summary': f'Reminder Opportunity',
                    'note': f'Dear Leader of {pipeline.team_id.name}, this opportunity day to close is longer than the average pipeline<br/>Day to Close : {pipeline.day_close_today}<br/>Average Day to Close : {average_day_close}',
                    'date_deadline': datetime.now(),
                    'user_id': pipeline.team_id.user_id.id,
                    'res_id': pipeline.id,
                    'res_model_id': self.env.ref('crm.model_crm_lead').id,
                    'activity_type_id': self.env.ref('project_todo.mail_activity_data_reminder').id
                })