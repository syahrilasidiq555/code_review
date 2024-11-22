# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import timedelta, datetime


STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approve1','Approved Manager'),
    ('approve2','Approved HR'),
    ('cancel','Canceled'),
    ('reject','Rejected'),
]   

class form_lupa_absen(models.Model):
    _name = "form.lupa.absen"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Lupa Absen'


    name = fields.Char('Name')

    def _get_default_employee(self):
        emp_id = self.env.user.employee_id
        return emp_id

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_get_default_employee, required=True, tracking=True)
    nik = fields.Char(related="employee_id.barcode", string="NIK")
    job_id = fields.Many2one(related='employee_id.job_id', string="Job Position")
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    section = fields.Many2one(related='employee_id.section', string='Section')
    work_location_id = fields.Many2one(related="employee_id.work_location_id", string='Unit')
    resource_calendar_id = fields.Many2one(related="employee_id.resource_calendar_id", string='Working Times')

    date = fields.Date('Date', default=datetime.now().date(), required=True)

    check_in = fields.Datetime(string='Check In', required=True, tracking=True)
    check_out = fields.Datetime(string='Check Out', required=True, tracking=True)
    attendance_from = fields.Selection([
        ('fingerprint', 'Fingerprint Machine'),
        ('odoo','ODOO')
    ], string='Attendance From', required=True, tracking=True)

    reason = fields.Text('Reason')
    documents = fields.Many2many('ir.attachment', string='Attachments')


    # UNTUK APPROVAL
    def _get_default_manager(self):
        emp_id = self.env.user.employee_id.parent_id
        return emp_id
    
    def _get_default_hr(self):
        emp_id = False
        group_hr = self.env.ref('hr.group_hr_manager')
        if group_hr and group_hr.users:
            emp_id = group_hr.users[0].employee_id.id if group_hr.users[0].employee_id else False
        return emp_id
    
    manager_id = fields.Many2one('hr.employee', string='Manager', default=_get_default_manager, tracking=True)
    hr_responsible_id = fields.Many2one('hr.employee', string='HR Responsible', default=_get_default_hr, tracking=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            record.manager_id = record.employee_id.parent_id



    approval_ids = fields.One2many('form.lupa.absen.approval.line','form_id', string='Approval Line')

    state = fields.Selection(STATE,
        string='State',
        default='draft',
        readonly=True,
        required=True, tracking=True)    

    state_cancel = fields.Selection(related="state", tracking=False)
    state_reject = fields.Selection(related="state", tracking=False)


    @api.model
    def create(self, values):
        values['name'] =  self.env['ir.sequence'].get_sequence(self._name, 'FLA')
        res = super(form_lupa_absen,self).create(values)
        return res
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Tidak bisa menghapus data dengan state selain DRAFT!'))
            res = super(form_lupa_absen,self).unlink()
            return res
        

    def create_replace_attendance(self):
        for record in self:
            # get overlap attendance and delete it
            attendances = self.env['hr.attendance'].sudo().search([
                ('employee_id','=', record.employee_id.id),
                ('check_out','>=', record.check_in),
                ('check_in','<=', record.check_out),
            ])
            if attendances:
                attendances.sudo().unlink()
            
            # create another attendances
            attendance = self.env['hr.attendance'].sudo().create({
                'employee_id':record.employee_id.id,
                'check_in': record.check_in,
                'check_out': record.check_out,
                'attendance_from':record.attendance_from,
                'form_lupa_absen_id': record.id,
            })

    ###############################################
    # Button
    ###############################################
    
            
    # RFA
    def action_rfa(self):
        for record in self:
            record.state = 'rfa'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # create schedule activity 
            if record.manager_id and record.manager_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Form Lupa Absen number {record.name} need your approval',
                    'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Overtime Management',
                    'date_deadline': datetime.now(),
                    'user_id': record.manager_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('custom_hr.model_form_lupa_absen').id,
                    'activity_type_id': 4 #to do
                })
    
    # Approve Manager
    def action_approve1(self):
        for record in self:
            record.state = 'approve1'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})
            
            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            # create schedule activity 
            if record.hr_responsible_id and record.hr_responsible_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Form Lupa Absen number {record.name} need your approval',
                    'summary': f'Dear HR Responsible of {record.employee_id.name}, we need your approval for Overtime Management',
                    'date_deadline': datetime.now(),
                    'user_id': record.hr_responsible_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('custom_hr.model_form_lupa_absen').id,
                    'activity_type_id': 4 #to do
                })
    
    # Approve HRD
    def action_approve2(self):
        for record in self:
            record.state = 'approve2'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            # create schedule activity 
            # if record.manager_id and record.manager_id.user_id:
            #     self.env['mail.activity'].create({
            #         'note': f'Form Lupa Absen number {record.name} need your approval',
            #         'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Overtime Management',
            #         'date_deadline': datetime.now(),
            #         'user_id': record.manager_id.user_id.id,
            #         'res_id': record.id,
            #         'res_model_id': self.env.ref('custom_hr.model_form_lupa_absen').id,
            #         'activity_type_id': 4 #to do
            #     })
                
            record.create_replace_attendance()


        
    # REVISE
    def action_revise(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_revise",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Revise Wizard',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }

            record.state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': 'revise',
                # 'closing_state': record.closing_state,
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # REJECT
    def action_reject(self):
        for record in self:
            record.state = 'reject'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # Cancel
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # Set to Draft
    def action_draft(self):
        for record in self:
            record.state = 'draft'

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")


# approval
class form_lupa_absen_approval_line(models.Model):
    _name = "form.lupa.absen.approval.line"
    _description = 'Overtime Management (Approval Line)'

    form_id = fields.Many2one('form.lupa.absen', string='Form Lupa Absen', ondelete="cascade")

    state = fields.Selection(STATE + [('revise','Revise')], string='State')    
    
    reason = fields.Text('Reason')

    pelaksana_id = fields.Many2one('res.users','Pelaksana', size=128)
    department_id = fields.Many2one(related='pelaksana_id.employee_id.department_id', string="Department")
    job_id = fields.Many2one(related='pelaksana_id.employee_id.job_id', string="Position")

    tanggal = fields.Datetime('Tanggal')