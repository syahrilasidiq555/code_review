from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class MasterUmk(models.Model):
    _name = 'master.umk'
    _description = "Master UMK/UMR"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']

    
    name = fields.Char(string='Name', required=True)
    umk_amount = fields.Float(string='Amount', required=True, tracking=True)
    current_umk_amount = fields.Float(compute='_compute_current_umk_amount', string='Current Amount')
    def _compute_current_umk_amount(self):
        for record in self:
            current_umk_amount = record.umk_amount
            if record.umk_history_ids:
                umk_history = record.umk_history_ids.filtered(lambda x: x.applied_date <= (datetime.now()+timedelta(hours=7)).date()).sorted(key=lambda r: r.applied_date, reverse=True)
                current_umk_amount = umk_history[0].umk_amount
            record.current_umk_amount = current_umk_amount

    # umk history
    umk_history_ids = fields.One2many('master.umk.history', 'umk_id', string='UMK History')


    def set_contract_history(self,umk_amount,date):
        for record in self:
            umk_history_ids = [[0,0,{
                'umk_amount': umk_amount,
                'applied_date': date,
            }]]
            # # validate applied date
            # if record.umk_history_ids and record.umk_history_ids.filtered(lambda x: x.applied_date == umk_history_ids[0][2]['applied_date']):
            #     raise ValidationError(f"You cannot assign the same applied date that already inserted in master umk! \n\n date : {umk_history_ids[0][2]['applied_date']}")
            # # validate umk amount
            # if record.umk_history_ids and record.umk_history_ids.filtered(lambda x: x.umk_amount == umk_history_ids[0][2]['umk_amount']):
            #     raise ValidationError(f"You cannot assign the same amount that already inserted in master umk! \n\n amount : {umk_history_ids[0][2]['umk_amount']}")

            record.umk_history_ids = umk_history_ids

    # def name_get(self):
    #     if not self.env.context.get("show_detail_amount", False):
    #         return super().name_get()
    #     vals = []
    #     for record in self:
    #         vals.append(tuple([record.id, f'{record.umk_amount} ({record.name})']))
    #     return vals

    def name_get(self):
        # if not self.env.context.get("show_detail_amount", False):
        #     return super().name_get()
        result = []
        for record in self:
            # umk_history = record.umk_history_ids.filtered(lambda x: x.applied_date <= (datetime.now()+timedelta(hours=7)).date()).sorted(key=lambda r: r.applied_date, reverse=True)
            name = f'Rp. {record.current_umk_amount:,} ({record.name})'
            result.append((record.id, name))
        return result
    
    # @api.model
    # def create(self, vals):
    #     result = super(MasterUmk, self).create(vals)
    #     if result:
    #         result.set_contract_history(result.umk_amount, result.create_date.date())
    #     return result
    
    ##########################################
    # ACTION BUTTON
    ##########################################
    def action_update_umk_amount(self):
        for record in self:
            okey = self._context.get('okey',False)
            umk_amount = self._context.get('umk_amount',0)
            applied_date = self._context.get('applied_date',False)
            if not okey:
                context = {
                    'default_umk_amount': record.umk_amount,
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_update_umk_amount",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Update Amount',
                    'res_model':'update.amount.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_payroll.update_amount_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
            record.umk_amount = umk_amount
            record.set_contract_history(umk_amount, applied_date)


class MasterUmkHistory(models.Model):
    _name = 'master.umk.history'
    _description = "Master UMK History"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']

    # head
    umk_id = fields.Many2one('master.umk', string='UMK')

    umk_amount = fields.Float(string='UMK', required=True, tracking=True)
    applied_date = fields.Date(string='Applied Date', required=True, tracking=True)


    def unlink(self):
        for record in self:
            if record.umk_id and record.umk_id.umk_amount == record.current_umk_amount:
                raise ValidationError(f"You cannot delete amount that has been set!\n\n amount: {record.umk_amount}")
            res = super(MasterUmkHistory,self).unlink()
            return res