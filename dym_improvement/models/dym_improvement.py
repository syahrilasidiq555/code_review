import time
from datetime import datetime

import json
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

# from odoo.osv import osv
import logging 


class dym_improvement(models.Model):
    _name = 'dym.improvement'
    _description = 'Improvement (QCC, QCP, dll)'
    

    def _get_default_department(self):
        dep_id = self.env.user.employee_id.department_id.id
        return self.env['hr.department'].search([('id','=',dep_id)])
    
    def _get_default_employee(self):
        emp_id = self.env.user.employee_id
        return emp_id

    name = fields.Char(string='Name')
    team_name = fields.Char(string='Nama Team / Project', required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    department_ids = fields.Many2many('hr.department', 'improvement_departments_rel','improvement_id','department_id', string='Dept/Cabang', default=_get_default_department, required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    pic = fields.Many2one('hr.employee', 'PIC', default=_get_default_employee, required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    loc_improvement = fields.Char(string='Lokasi Improvement', required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    tema_improvement = fields.Char(string='Tema Improvement', required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    bulan_pendaftaran = fields.Date('Bulan Pendaftaran', required=True, default=datetime.now().date(), readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})

    team_ids = fields.Many2many('res.users', 'improvement_users_rel','imp_id','team_id', string='Member List', readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})




    # Step Improvement
    deskripsi_plan = fields.Text(string='Deskripsi Improvement', required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    improvement_line_plan_ids = fields.One2many('dym.improvement.line.plan','improvement_id', string='Improvement Line Plan', ondelete='cascade', readonly=True, states={'new': [('readonly', False)]})
    improvement_line_ids = fields.One2many('dym.improvement.line','improvement_id',string='Improvement Line', ondelete='cascade')


    # Estimasi, Cost, and Benefit
    # Estimasi Biaya
    estimasibiaya_lines = fields.One2many('dym.improvement.estimasibiaya.line', 'imp_id', string='Resiko', readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    # total_biaya_estimasi = fields.Integer(string='Total Estimasi', compute='_compute_total_biaya_estimasi', store=True)


    # Cost and Benefit
    hasil_cost_lines = fields.One2many('dym.improvement.hasil.cost.line', 'imp_id', string='Hasil Perhitungan Cost', readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    hasil_benefit_lines = fields.One2many('dym.improvement.benefit.line', 'imp_id', string='Hasil Perhitungan Benefit', readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})

    total_cost = fields.Integer('Total Cost', compute='_compute_hasil_cost_benefit', store=True)
    total_benefit = fields.Integer('Total Benefit', compute='_compute_hasil_cost_benefit', store=True)
    total_ratio = fields.Float('Total Ratio', compute='_compute_hasil_cost_benefit', store=True)
    ratio_percentage = fields.Char('Ratio Percentage', compute='_compute_hasil_cost_benefit', store=True)


    # Approval Line
    approval_ids = fields.One2many('dym.improvement.approval.line','imp_id', string='Improvement Approval Line')
    

    # Selection
    jenis_improvement = fields.Selection(
        [('qcc','QCC'),
        ('qcp','QCP'),
        ('qcl','QCL'),
        ('pps','PPS'),
        ('fiver','5R'),
        ('safety_improvement','Safety Improvement')],
        string='Jenis Improvement',
        required=True, readonly=True, states={'new': [('readonly', False)], 'revise': [('readonly', False)], 'in_progress': [('readonly', False)]})
    level = fields.Selection(
        [('bronze','BRONZE'),
        ('silver','SILVER'),
        ('gold','GOLD')],
        string='Level')
    state_improvement = fields.Selection(
        [('new','New'),
        ('step1','Menentukan Tema'),
        ('step2','Analisa Situasi'),
        ('step3','Menetapkan Target'),
        ('step4','Analisa Penyebab'),
        ('step5','Merencanakan Penanggulangan'),
        ('step6','Melaksanakan Penanggulangan'),
        ('step7','Evaluasi Hasil'),
        ('step8','Standarisasi & tindak Lanjut'),
        ('finish','Finish')],
        string='State Improvement',
        default='new')
    
    step_id = fields.Many2one('improvement.step', string='Step')

    state = fields.Selection(
        [('new','New'),
        ('rfa','Request of Approval'),
        ('in_progress','In Progress'),
        ('done','Done'),
        ('refuse','Refused'),
        ('revise','Revised')],
        string='State',
        default='new',
        readonly=True,
        required=True)
    state_refuse = fields.Selection(related='state', string='State')
    state_revise = fields.Selection(related='state', string='State')
    rel_level = fields.Selection(related='level', string='Level')


    # PIC IMPROVEMENT
    hasil_cost_lines_pic_imp = fields.One2many('dym.improvement.hasil.cost.line.pic_imp', 'imp_id', string='Hasil Perhitungan Cost')
    hasil_benefit_lines_pic_imp = fields.One2many('dym.improvement.benefit.line.pic_imp', 'imp_id', string='Hasil Perhitungan Benefit')
    
    total_cost_pic_imp = fields.Integer(compute='_compute_hasil_cost_benefit_pic_imp', string='Total Cost', store=True)
    total_benefit_pic_imp = fields.Integer(compute='_compute_hasil_cost_benefit_pic_imp', string='Total Benefit', store=True)
    total_ratio_pic_imp = fields.Float(compute='_compute_hasil_cost_benefit_pic_imp', string='Total Ratio', store=True)
    ratio_percentage_pic_imp = fields.Char(compute='_compute_hasil_cost_benefit_pic_imp', string='Ratio Percentage', store=True)

    # PIC IMPROVEMENT
    @api.depends('hasil_cost_lines_pic_imp','hasil_benefit_lines_pic_imp')
    def _compute_hasil_cost_benefit_pic_imp(self):
        for record in self:
            record.total_ratio_pic_imp = 0
            record.ratio_percentage_pic_imp = '0'

            if record.hasil_cost_lines_pic_imp:
                total = 0
                for x in record.hasil_cost_lines_pic_imp:
                    total += x.biaya
                record.total_cost_pic_imp = total
            else:
                record.total_cost_pic_imp = 0

            if record.hasil_benefit_lines_pic_imp:
                total = 0
                for x in record.hasil_benefit_lines_pic_imp:
                    total += x.benefit
                record.total_benefit_pic_imp = total
            else:
                record.total_benefit_pic_imp = 0


            record.total_ratio_pic_imp = record.total_benefit_pic_imp - record.total_cost_pic_imp
            if record.total_cost_pic_imp > 0 :
                ratio_percentage_pic_imp = record.total_benefit_pic_imp / record.total_cost_pic_imp * 100
                record.ratio_percentage_pic_imp = str(round(ratio_percentage_pic_imp, 2))+"%"
            else:
                record.ratio_percentage_pic_imp = 'INFINITY'
    
    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get_sequence(self._name, 'IMP')

        if not values['jenis_improvement']:
            raise ValidationError(_('Field Jenis Improvement Belum diisi!'))

        crfs = super(dym_improvement,self).create(values)
        return crfs

    def unlink(self):
        for record in self:
            if record.state != 'new':
                raise ValidationError(_('Tidak bisa menghapus data dengan state selain new!'))
            res = super(dym_improvement,self).unlink()
            return res
    

    @api.onchange('jenis_improvement')
    def _onchange_jenis_improvement(self):
        for record in self:
            step_ids = self.env['improvement.step'].search([('jenis_improvement','=',record.jenis_improvement),('active','!=',False)], order="sequence asc")
            
            # get step id
            record.step_id = step_ids[0].id if step_ids else None

            # get improvement step plan based on jenis improvement
            record.improvement_line_plan_ids = None
            if step_ids:
                plan_ids = []
                imps_plan = self.env['dym.improvement.line.plan']
                for step_id in step_ids:
                    plan = imps_plan.create({'step_id':step_id.id})
                    plan_ids.append(plan.id)
                record.improvement_line_plan_ids = plan_ids if plan_ids else None

            
            # get improvement step based on jenis improvement
            if step_ids:
                record.improvement_line_ids = None
                improvement_line_ids = []
                imps = self.env['dym.improvement.line']
                imp = imps.create({'step_id':step_ids[0].id})
                improvement_line_ids.append(imp.id)
                record.improvement_line_ids = improvement_line_ids
                

    @api.onchange('improvement_line_plan_ids')
    def change_tema_improvement(self):
        for record in self:            
            if len(record.improvement_line_plan_ids)>=1:
                if record.step_id.id == record.improvement_line_plan_ids[0].step_id.id:
                    step1 = record.improvement_line_plan_ids[0]
                    if step1.due_date and step1.due_date != record.improvement_line_ids[0].due_date: 
                        record.improvement_line_ids = None

                        imps = self.env['dym.improvement.line']
                        data=[]
                        imp_result = {
                            'step_id': step1.step_id.id,
                            'due_date':step1.due_date,
                            'state':'draft'
                        }
                        sr = imps.create(imp_result)
                        data.append(sr.id)
                        
                        record.improvement_line_ids = data

    @api.depends('hasil_cost_lines','hasil_benefit_lines')
    def _compute_hasil_cost_benefit(self):
        for record in self:
            record.total_ratio = 0
            record.ratio_percentage = '0'
            # raise ValidationError(_('you are here')) 

            if record.hasil_cost_lines:
                total = 0
                for x in record.hasil_cost_lines:
                    total += x.biaya
                record.total_cost = total
            else:
                record.total_cost = 0

            if record.hasil_benefit_lines:
                total = 0
                for x in record.hasil_benefit_lines:
                    total += x.benefit
                record.total_benefit = total
            else:
                record.total_benefit = 0

            # if record.total_cost and record.total_benefit:

            record.total_ratio = record.total_benefit - record.total_cost
            if record.total_cost > 0 :
                ratio_percentage = record.total_benefit / record.total_cost * 100
                record.ratio_percentage = str(round(ratio_percentage, 2))+"%"
            else:
                record.ratio_percentage = 'INFINITY'

    # ----------Scheduled Action
    def cron_mail_reminder_improvement(self):
        date_now = datetime.now().date()
        count = 0
        improvement_obj = self.env['dym.improvement'].search([('state','!=','done')])
        for record in improvement_obj:
            for data in record.improvement_line_ids:
                if data.state != 'approved' and data.state != 'refuse':
                    if data.due_date:
                        if date_now >= data.due_date:
                            try:
                                record.send_mail_notification_pic(state='reminder')
                                count += 1
                            except:
                                pass
        # raise ValidationError(_("email sent : "+str(count)))
        
    # ----------


    def send_mail_notification_pic(self,state):
        for record in self:
            for data in record.improvement_line_ids:
                if data.state != 'approved':
                    context = {}

                    template = False
                    if not template:
                        template = self.env.ref('dym_improvement.dym_improvement_mail_notification')
                    assert template._name == 'mail.template'

                    email_user = ''

                    if state == 'rfa':
                        context['status'] = 'REQUEST FOR APPROVAL'
                        context['improvement_name'] = record.name
                        context['jenis_improvement'] = dict(record._fields['jenis_improvement'].selection).get(record.jenis_improvement)
                        context['step_improvement'] = record.step_id.name
                        context['desc'] = data.desc
                        context['pic_name'] = record.pic.parent_id.name
                        context['pic_dep'] = record.pic.parent_id.department_id.name
                        # context['url'] = 'https://192.168.3.55/web#id=%s&action=917&model=dym.improvement&view_type=form&cids=1&menu_id=693' % str(record.id)
                        context['url'] = ''
                        lang  = record.pic.parent_id.user_id.lang
                    elif state == 'approve' or state == 'revise' or state == 'reminder':
                        if state == 'approve':
                            context['status'] = 'DRAFT'
                        elif state == 'revise':
                            context['status'] = 'REVISED'
                        elif state == 'reminder':
                            context['status'] = 'REMINDER TO FOLLOW UP (Higher than Due Date)'
                        context['improvement_name'] = record.name
                        context['jenis_improvement'] = dict(record._fields['jenis_improvement'].selection).get(record.jenis_improvement)
                        context['step_improvement'] = record.step_id.name
                        context['desc'] = data.desc
                        context['pic_name'] = record.pic.name
                        context['pic_dep'] = record.pic.department_id.name
                        # context['url'] = 'https://192.168.3.55/web#id=%s&action=917&model=dym.improvement&view_type=form&cids=1&menu_id=693' % str(record.id)
                        context['url'] = '' % str(record.id)
                        email_user = record.pic.work_email
                        lang  = record.pic.user_id.lang
                        


                    if email_user:
                        # raise exceptions.UserError(_("Cannot send email: parent %s has no email address.") % self.parent_id.name)
                        with self.env.cr.savepoint():
                            force_send = not(self.env.context.get('import_file', False))
                            email_user = 'syahrilasidiq555@gmail.com'
                            template.with_context(lang=lang, context=context, email_to=email_user).send_mail(self.id, force_send=force_send, raise_exception=True)
                            # template.send_mail(self.id, force_send=force_send, raise_exception=True)


    def check_user(self):
        emp_id = self.env.user.employee_id
        if emp_id.id == self.pic.id :
            if not self.env.user.has_group('suggestion_system.group_suggestion_system_pic_improvement'):
                raise ValidationError(_('Tidak Bisa Approve Data Diri Sendiri!'))



    # Button Action Workflow
    def action_rfa(self):
        for record in self:
            if not record.estimasibiaya_lines:
                raise ValidationError(_('Field Resiko harus diisi terlebih dahulu!'))

            if not record.hasil_cost_lines or not record.hasil_benefit_lines:
                raise ValidationError(_('Field Cost dan Benefit Harus diisi Terlebih dahulu!'))
                
            last_improvement = record.improvement_line_ids[len(record.improvement_line_ids)-1]
            if not last_improvement.desc or not last_improvement.due_date:
                raise ValidationError(_('Field Deskripsi atau Due Date pada Step terbaru belum diisi!'))

            plan_count = len(record.improvement_line_plan_ids)
            count = 0
            for plan in record.improvement_line_plan_ids:
                if plan.due_date:
                    count += 1
            if plan_count != count :
                raise ValidationError(_('Anda Harus Mengisi Semua Tanggal Selesai Pada Rencana Improvement!'))

            try:
                record.send_mail_notification_pic(state='rfa')
            except:
                pass
            last_improvement.state = 'rfa'
            record.write({'state':'rfa'})

    def action_next_step(self):
        for record in self:
            record.check_user()
        
        if record.total_ratio < 0:
                raise ValidationError(_("Proses Approve tidak dapat dilakukan karena Total NQI (Benefit) < 0! "))
        
        approval_line_ids = []
        improvement_line_ids = []
        step_id_now = None
        state = None
        for i,imp_line in enumerate(record.improvement_line_ids):
            if imp_line.state == 'rfa':
                # write jadi approve di linenya
                imp_line.write({'state':'approved'})
                # approval line
                approval_line_ids.append([0,0,{
                        'step_id':imp_line.step_id.id,
                        'pelaksana_id':self._uid,
                        'sts':'3',
                        'tanggal':datetime.today(),
                    }])
                # cek apa step selanjutnya
                for j, plan in enumerate(record.improvement_line_plan_ids):
                    
                    if j == len(record.improvement_line_plan_ids)-1:
                        # jika statenya done
                        state = 'done'
                        record.write({'state':'done'})
                        break
                    elif imp_line.step_id.id == plan.step_id.id:
                        # buat line baru improvement
                        improvement_line_ids.append([0,0,{
                            'step_id': record.improvement_line_plan_ids[j+1].step_id.id,
                            'due_date':record.improvement_line_plan_ids[j+1].due_date,
                            'state':'draft'
                        }])
                        # untuk stage workflow
                        step_id_now = record.improvement_line_plan_ids[j+1].step_id.id
                        state = 'in_progress'
                        record.write({'state':state,'step_id':step_id_now,'improvement_line_ids':improvement_line_ids,'approval_ids':approval_line_ids})

                        break
                
                try:
                    record.send_mail_notification_pic(state='approve')
                except:
                    pass
                break

    def action_next_step2(self):
        for record in self:
            record.check_user()
            if record.total_ratio < 0:
                raise ValidationError(_("Proses Approve tidak dapat dilakukan karena Total NQI (Benefit) < 0! "))

            state_improvement = record.state_improvement
            last_improvement = record.improvement_line_ids[len(record.improvement_line_ids)-1].tipe
            # step = ''
            # if state_improvement == 'new':
            #     step = 0
            # else:
            step = int(last_improvement.replace('step',''))


            plan_date = None
            next_step = 'step'+ str(int(last_improvement.replace('step',''))+1)
            for x in record.improvement_line_plan_ids:
                if next_step == x.tipe:
                    plan_date = x.due_date

            approval_line_ids = []
            improvement_line_vals = []        
            if record.state_improvement == 'step8':
                for data in record.improvement_line_ids:
                    if data.state == 'rfa':
                        data.write({'state':'approved'})
                approval_line_ids.append([0,0,{
                            'step':'step8',
                            'pelaksana_id':self._uid,
                            'sts':'3',
                            'tanggal':datetime.today(),
                        }])
                record.write({'state':'done','state_improvement':'finish'})
            else:
                # if record.state_improvement == 'new':
                #     si = 'step'+str(step+2)
                #     si_approval = 'step'+str(step+1)
                # else:
                si = 'step'+str(step+1)
                si_approval = last_improvement
                improvement_line_vals = []
                improvement_line_vals.append([0,0,{
                            'tipe':si,
                            'due_date':plan_date
                        }])
                for data in record.improvement_line_ids:
                    if data.state == 'rfa':
                        data.write({'state':'approved'})
                
                approval_line_ids.append([0,0,{
                            'step':si_approval,
                            'pelaksana_id':self._uid,
                            'sts':'3',
                            'tanggal':datetime.today(),
                        }])
                record.write({'state':'in_progress','state_improvement':si,'improvement_line_ids':improvement_line_vals,'approval_ids':approval_line_ids})
            try:
                record.send_mail_notification_pic(state='approve')
            except:
                pass

    def action_refuse(self):
        for record in self:
            record.check_user()
            approval_line_ids = []

            last_improvement = record.improvement_line_ids[len(record.improvement_line_ids)-1]
            approval_line_ids.append([0,0,{
                        'step':last_improvement.tipe,
                        'pelaksana_id':self._uid,
                        'sts':'4',
                        'tanggal':datetime.today(),
                    }])
            last_improvement.write({'state':'refuse'})
            record.write({'state':'refuse','approval_ids':approval_line_ids})

    def action_revise(self):
        for record in self:
            record.check_user()
            last_improvement = record.improvement_line_ids[len(record.improvement_line_ids)-1]
            okey = record._context.get('okey',False)
            text = record._context.get('text','')
            if not okey:
                context = {
                    'default_imp_id':record.id
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Revise Reason',
                    'res_model':'wizard.revise.dym.improvement',
                    'view_type':'form',
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                        'step_id':last_improvement.step_id.id,
                        'pelaksana_id':self._uid,
                        'reason':text,
                        'sts':'5',
                        'tanggal':datetime.today(),
                    }])
            last_improvement.write({'state':'revise'})
            record.write({'state':'revise', 'approval_ids':approval_line_ids}) 
            try:
                record.send_mail_notification_pic(state='revise')
            except:
                pass
            return True



# Improvement And its Attachment
class dym_improvement_line(models.Model):
    _name = "dym.improvement.line"
    _description = 'dym improvement (line)'

    # name = 
    improvement_id = fields.Many2one('dym.improvement', string='Improvement')
    desc = fields.Text(string='Deskripsi', readonly=True, states={'draft': [('readonly', False)], 'revise': [('readonly', False)]})
    due_date = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)], 'revise': [('readonly', False)]})
    attachment_ids = fields.One2many('dym.improvement.line.attachment', 'improvement_line_id', string='Improvement Attachment', ondelete='cascade', readonly=True, states={'draft': [('readonly', False)], 'revise': [('readonly', False)]})
    tipe = fields.Selection(
        [('step1','Menentukan Tema'),
        ('step2','Analisa Situasi'),
        ('step3','Menetapkan Target'),
        ('step4','Analisa Penyebab'),
        ('step5','Merencanakan Penanggulangan'),
        ('step6','Melaksanakan Penanggulangan'),
        ('step7','Evaluasi Hasil'),
        ('step8','Standarisasi & tindak Lanjut')],
        string='Step')
    
    step_id = fields.Many2one('improvement.step', string='Step')


    state = fields.Selection(
        [('draft','Draft'),
        ('rfa','Request for Approval'),
        ('approved','Approved'),
        ('refuse','Refused'),
        ('revise','Revised')],
        string='State',
        default='draft',
        readonly=True,
        required=True)
    state_refuse = fields.Selection(related='state', string='State')
    state_revise = fields.Selection(related='state', string='State')


class dym_improvement_line_plan(models.Model):
    _name = "dym.improvement.line.plan"
    _description = 'dym improvement (plan line)'

    # name = 
    improvement_id = fields.Many2one('dym.improvement', string='Improvement')
    due_date = fields.Date(string='Rencana Selesai')
    tipe = fields.Selection(
        [('step1','Menentukan Tema'),
        ('step2','Analisa Situasi'),
        ('step3','Menetapkan Target'),
        ('step4','Analisa Penyebab'),
        ('step5','Merencanakan Penanggulangan'),
        ('step6','Melaksanakan Penanggulangan'),
        ('step7','Evaluasi Hasil'),
        ('step8','Standarisasi & tindak Lanjut')],
        string='Step')
    step_id = fields.Many2one('improvement.step', string='Step')
    
   


class dym_improvement_line_attachment(models.Model):
    _name = "dym.improvement.line.attachment"
    _description = 'dym improvement (line attachment)'

    # task_id = fields.Many2one('project.task','Project Task')
    improvement_line_id = fields.Many2one('dym.improvement.line','Improvemenet Line')
    description = fields.Char('Description')
    attachment = fields.Binary('Attachment', required=True)
    attachment_name = fields.Text('Attachment Name')
    attachment_view = fields.Binary(related='attachment', string='Attachment view')


# Cost and Benefit
class dym_improvement_estimasiBiaya(models.Model):
    _name = 'dym.improvement.estimasibiaya.line'
    _description = 'Improvement (Estimasi Resiko )'

    imp_id = fields.Many2one('dym.improvement','Improvement')
    deskripsi_biaya = fields.Char('Deskripsi', required=True)
    biaya = fields.Integer('Biaya')

class dym_improvement_hasil_cost(models.Model):
    _name = 'dym.improvement.hasil.cost.line'
    _description = "Improvement (Hasil Cost)"

    imp_id = fields.Many2one('dym.improvement','Improvement')
    deskripsi_biaya = fields.Char('Deskripsi', required=True)
    biaya = fields.Integer('Biaya', required=True)

class dym_improvement_benefit(models.Model):
    _name = 'dym.improvement.benefit.line'
    _description = "Improvement (benefit)"

    imp_id = fields.Many2one('dym.improvement','Improvement')
    deskripsi_biaya = fields.Char('Deskripsi', required=True)
    benefit = fields.Integer('benefit', required=True)


# PIC IMPROVEMENT
class dym_improvement_hasil_cost_pic_imp(models.Model):
    _name = 'dym.improvement.hasil.cost.line.pic_imp'
    _description = "Improvement (Hasil Cost)"

    imp_id = fields.Many2one('dym.improvement','Improvement')
    deskripsi_biaya = fields.Char('Deskripsi', required=True)
    biaya = fields.Integer('Biaya', required=True)

class dym_improvement_benefit_pic_imp(models.Model):
    _name = 'dym.improvement.benefit.line.pic_imp'
    _description = "Improvement (benefit)"

    imp_id = fields.Many2one('dym.improvement','Improvement')
    deskripsi_biaya = fields.Char('Deskripsi', required=True)
    benefit = fields.Integer('benefit', required=True)



# Page Approval
class dym_improvement_approval_line(models.Model):
    _name = "dym.improvement.approval.line"
    _description = 'dym improvement (approval)'

    imp_id = fields.Many2one('dym.improvement','Improvement')
    form_id = fields.Many2one('ir.model','Form')
    group_id = fields.Many2one('res.groups','Group', select=True)
    limit = fields.Float('Limit', digits=(12,2))
    sts = fields.Selection([('1','Draft'),('2','Request for Approval'),('3','Approved'),('4','Refused'),('5','Revised')],string='Status')
    step = fields.Selection(
        [('step1','Menentukan Tema'),
        ('step2','Analisa Situasi'),
        ('step3','Menetapkan Target'),
        ('step4','Analisa Penyebab'),
        ('step5','Merencanakan Penanggulangan'),
        ('step6','Melaksanakan Penanggulangan'),
        ('step7','Evaluasi Hasil'),
        ('step8','Standarisasi & tindak Lanjut')],
        string='Status')
    step_id = fields.Many2one('improvement.step', string='Step')
    
    reason = fields.Text('Reason')
    pelaksana_id = fields.Many2one('res.users','Pelaksana', size=128)
    rel_department = fields.Many2one(related='pelaksana_id.employee_id.department_id', string="Department")
    rel_job = fields.Many2one(related='pelaksana_id.employee_id.job_id', string="Position")
    tanggal = fields.Datetime('Tanggal')