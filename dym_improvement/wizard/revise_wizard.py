from odoo import models, api,fields
from odoo.osv import osv

# Wizard Confirm Button
class wizard_revise_improvement(models.TransientModel):
    _name = "wizard.revise.dym.improvement"

    imp_id = fields.Many2one('dym.improvement', 'Improvement')
    text =  fields.Text()

    # @api.multi
    def action_yes(self):
        # return True
        # self.env['dym.stock.packing'].post()
        # self.env['dym.stock.packing'].search([('id','=',self.ss_id.id)]).post()
        self.env['dym.improvement'].search([('id','=',self.imp_id.id)]).with_context(okey=True,text=self.text).action_revise()
        
wizard_revise_improvement()