# -*- coding: utf-8 -*-
import jinja2
import json
import base64
import os

from datetime import datetime, timedelta, date
from dateutil import parser

import odoo
from odoo import http, models, fields, _
from odoo.http import request, route

def remove_b64(text):
    return str(text)[2:-1]

def get_dict(text):
    return dict(text)

def date_indonesia(date_value):
    return date_value + timedelta(hours=7)

def date_indonesia_save(date_value):
    return date_value - timedelta(hours=7)

# if hasattr(sys, 'frozen'):
#     # When running on compiled windows binary, we don't have access to package loader.
#     path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
#     loader = jinja2.FileSystemLoader(path)
# else:
#     loader = jinja2.PackageLoader('odoo.addons.web', "views")

path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
loader = jinja2.FileSystemLoader(path)

env = jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps
env.filters['remove_b64'] = remove_b64
env.filters['dict'] = get_dict
env.filters['json_load'] = json.loads
env.filters['date_indonesia'] = date_indonesia

class EmployeePortalNew(http.Controller):
    def _handle_attachments(self, active_model, active_id, documents):
        attachment_ids = []
        for document in documents:
            dataUrl = document['file']
            arr = dataUrl.split(',')
            file_document = arr[1]

            attachment = request.env['ir.attachment'].sudo().create({
                'name': document['name'],
                'type': 'binary',
                'res_id': active_id,
                'res_model': active_model,
                'datas': file_document,
                'public': True if active_model == 'hr.leave' else False,
            })
            attachment_ids.append(attachment.read(['id', 'name','website_url','file_size']))

        return attachment_ids
    

    def _middleware_related_employee(self):
        # return request.redirect('/')
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': '404',
            'description':'Not Found',
        }
        return env.get_template("404.html").render(data)
        

    # MAIN MENU
    @http.route(['/portals/home','/portals'], type='http', auth="user", method=['GET'])
    def render_portal_home(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()

        menus = []
        menus.append({
            'name': 'Expenses',
            'url': '/portals/expense',
            'icon_url' : '/hr_expense/static/description/icon.png'
        })
        menus.append({
            'name': 'My Account',
            'url': '/portals/me',
            'icon_url' : '/hr/static/description/icon.png'
        })
        menus.append({
            'name': 'My Attendance',
            'url': '/portals/attendance',
            'icon_url' : '/hr_attendance/static/description/icon.png'
        })
        if request.env.user.employee_id.is_approve_attendance:
            menus.append({
                'name': 'Approve Attendance',
                'url': '/portals/attendance_approve',
                'icon_url' : '/approvals/static/description/icon.png'
            })

        menus.append({
            'name': 'My Time-Off',
            'url': '/portals/time-off',
            'icon_url' : '/hr_holidays/static/description/icon.png'
        })

        if request.env.user.employee_id.is_approve_attendance:
            menus.append({
                'name': 'Approve Time-Off',
                'url': '/portals/time-off_approve',
                'icon_url' : '/social/static/description/icon.png'
            })

        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Portal Menu',
            'description':'Welcome To Portal',
            'menus':menus
        }
        return env.get_template("index.html").render(data)
    
    # EXPENSE LIST
    @http.route('/portals/expense', type='http', auth="user", method=['GET'])
    def render_portal_expense(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Expenses',
            'description':'Welcome To Expense',
            # 'expenses': request.env['hr.expense'].web_search_read([('employee_id','=',request.env.user.employee_id.id)], ['date', 'name', 'employee_id', 'payment_mode', 'currency_id', 'total_amount', 'state'], order="date desc")
            # 'expenses': request.env['hr.expense'].search([],limit=500),
            'expenses': request.env['hr.expense'].search([('employee_id','=',request.env.user.employee_id.id)],limit=500, order="date desc"),
            'expenses_fields': request.env['hr.expense'].sudo().fields_get(['payment_mode','state'],['selection'])
        }
        return env.get_template("expense.html").render(data)
    
    # EXPENSE CREATE
    @http.route('/portals/expense/create', type='http', auth="user", method=['GET'])
    def render_portal_expense_create(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Create New Expense',
            'description':'Welcome To Expense',
            'products': request.env['product.product'].sudo().web_search_read([('can_be_expensed','=',True)], ['id', 'name']),
            'locations': request.env['hr.expense.location'].sudo().web_search_read([], ['id', 'name']),
        }
        return env.get_template("expense_create.html").render(data)
    
    # EXPENSE DETAIL/EDIT
    @http.route('/portals/expense/<int:exp_id>', type='http', auth="user", method=['GET'])
    def render_portal_expense_detail(self, exp_id, **kwargs):
        try:
            expense = request.env['hr.expense'].search([('id','=',exp_id),('employee_id','=',request.env.user.employee_id.id)],limit=1)
            # expense = request.env['hr.expense'].browse(exp_id)
            if expense:
                expense_attachments = request.env['ir.attachment'].sudo().search([('res_id', '=', expense[0].id), ('res_model', '=', 'hr.expense')]).read(['id', 'name','website_url','file_size'])
                # expense_attachments = request.env['ir.attachment'].search([])
                
                data = {
                    'user':request.env.user.read(['id','name','share'])[0],
                    'title': "Expense | "+ str(expense[0].name),
                    'description':'Welcome To Expense',
                    'expense': expense[0],
                    'expense_attachments':expense_attachments,
                    'products': request.env['product.product'].sudo().web_search_read([('can_be_expensed','=',True)], ['id', 'name']),
                    'locations': request.env['hr.expense.location'].sudo().web_search_read([], ['id', 'name']),
                }
                return env.get_template("expense_detail.html").render(data)
            else:
                return request.redirect('/portals/expense')
        except Exception as e:
            print("error get detail expense")
            print(e)
            return request.redirect('/portals/expense')
            # return request.render('http_routing.404')
            
    # MAIN MENU
    @http.route('/portals/me', type='http', auth="user", method=['GET'])
    def render_portal_my_account(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        group_team_approver = request.env['ir.model.data'].sudo().search([('module','=','hr_expense'),('name','=','group_hr_expense_team_approver')], limit=1)
        domain = ('groups_id','=',[group_team_approver[0].res_id]) if group_team_approver else None

        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'My Account',
            'description':'This is my account',
            'employee':request.env.user.employee_id,
            'departments': request.env['hr.department'].sudo().web_search_read([], ['id', 'name']),
            'jobs': request.env['hr.job'].sudo().web_search_read([], ['id', 'name']),
            'managers': request.env['hr.employee'].sudo().web_search_read([], ['id', 'name']),
            'work_locations': request.env['hr.work.location'].sudo().web_search_read([], ['id', 'name']),
            'work_addresses': request.env['res.partner'].sudo().web_search_read([('id','=',request.env.user.company_id.partner_id.id)], ['id', 'name'], order="name"),
            'addresses': request.env['res.partner'].sudo().web_search_read(['|',('company_id','=',False),('company_id','=',request.env.user.company_id.id)], ['id', 'name'], order="name"),
            'coaches': request.env['hr.employee'].sudo().web_search_read(['|',('company_id','=',False),('company_id','=',request.env.user.company_id.id)], ['id', 'name']),
            'expense_managers': request.env['res.users'].sudo().web_search_read([domain], ['id', 'name']),
            'resource_calendars': request.env['resource.calendar'].sudo().web_search_read(['|',('company_id','=',False),('company_id','=',request.env.user.company_id.id)], ['id', 'name']),
            'countries': request.env['res.country'].sudo().web_search_read([], ['id', 'name']),
            

            'fields_list': request.env['hr.employee'].sudo().fields_get(['tz','marital','certificate','gender'],['selection'])
        }
        return env.get_template("me.html").render(data)
    
    @http.route([
        '/portals/hr_expense/<string:action>',
        '/portals/hr_expense/<string:action>/<int:active_id>'
    ], type="json", auth="user", method=['POST'], csrf=False)
    def expense_crud(self, action, active_id=None, **kwargs):
        response = {
            'code': 99, 
            'status': 'error',
            'value': 'something went wrong!', 
        }
        if request.env.user.employee_id:
            values = kwargs.get('values')

            if action == 'create':
                try:
                    expense_id = request.env['hr.expense'].sudo().create({
                        'employee_id': request.env.user.employee_id.id,
                        'name': values['name'],
                        'product_id': values['product_id'],
                        'date': values['date'],
                        'unit_amount': values['unit_amount'],
                        'quantity': values['quantity'],
                        'expense_location': values['expense_location'],
                        'description': values['description'],
                    })

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully created the record!',
                        'id' : expense_id.id,
                    }

                    if kwargs['documents']:
                        attachment_ids = self._handle_attachments(active_model='hr.expense', active_id=expense_id.id, documents=kwargs['documents'])
                        response['attachment_ids'] = attachment_ids

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            
            if action == 'update':
                try:
                    expense_id = request.env['hr.expense'].browse(active_id)
                    if expense_id and expense_id.state == 'draft':
                        expense_id.update(values)

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : expense_id.id,
                        }

                        if kwargs['documents']:
                            attachment_ids = self._handle_attachments(active_model='hr.expense', active_id=expense_id.id, documents=kwargs['documents'])
                            response['attachment_ids'] = attachment_ids
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only edit record that has 'To Submit' State!",
                            'id' : expense_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
                
            
            if action == 'delete':
                try:
                    expense_id = request.env['hr.expense'].browse(active_id)
                    if expense_id and expense_id.state == 'draft':
                        expense_id.unlink()

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully deleted the record!',
                            'id' : expense_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only delete 'To Submit' Expense!" if expense_id and expense_id.state != 'draft' else 'Record not found!',
                            'id' : expense_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

        # return json.dumps(response)
        return response
    
    @http.route([
        '/portals/ir_attachment/delete/<int:active_id>'
    ], type="json", auth="user", method=['POST'], csrf=False)
    def attachment_delete(self, active_id, **kwargs):
        response = {
            'code': 99, 
            'status': 'error',
            'value': 'something went wrong!', 
        }
        if request.env.user.employee_id:
            try:
                print("MASUK ATTACHMENT_DELETE")
                attachment_id = request.env['ir.attachment'].browse(active_id)
                print("attachment_id = ", attachment_id)
                print("attachment_id.res_model = ", attachment_id.sudo().res_model)
                if attachment_id:
                    if (attachment_id.sudo().res_model == 'hr.expense' or attachment_id.sudo().res_model == 'hr.leave') and attachment_id.sudo().res_id:
                        dt = request.env[attachment_id.sudo().res_model].browse(attachment_id.res_id)

                        if attachment_id.sudo().res_model == 'hr.expense':
                            if dt.state == 'draft':
                                attachment_id.sudo().unlink()
                                response = {
                                    'code': 0, 
                                    'status': 'success',
                                    'message': 'You have successfully deleted the record!',
                                }
                            else:
                                response = {
                                    'code': 0, 
                                    'status': 'failed',
                                    'message': 'You cannot delete not-Draft Expense!',
                                }

                    if attachment_id.sudo().res_model == 'hr.leave':
                        if dt.state in ['draft','confirm']:
                            attachment_id.sudo().unlink()
                            response = {
                                'code': 0, 
                                'status': 'success',
                                'message': 'You have successfully deleted the record!',
                            }
                        else:
                            response = {
                                'code': 0, 
                                'status': 'failed',
                                'message': 'You cannot delete not-Draft Expense!',
                            }
                            
                else:
                    response = {
                        'code': 0, 
                        'status': 'failed',
                        'message': 'Record not found!',
                    }

            except Exception as e:
                print("errorr")
                print(e)
                request.env.cr.rollback()
                errmsg = str(e).replace('\"', '')
                response = {
                    'code': 0, 
                    'status': 'error',
                    'id': active_id, 
                    'value': 'something went wrong!', 
                    'message': errmsg
                }

        # return json.dumps(response)
        return response


    @http.route([
        '/portals/hr_employee/<string:action>/me'
    ], type="json", auth="user", method=['POST'], csrf=False)
    def hr_employee_crud(self, action, **kwargs):
        response = {
            'code': 99, 
            'status': 'error',
            'value': 'something went wrong!', 
        }
        if request.env.user.employee_id:
            values = kwargs.get('values')

            if action == 'update':
                try:
                    employee_id = request.env['hr.employee'].browse(request.env.user.employee_id.id)
                    if employee_id:
                        employee_id.sudo().update(values)

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : employee_id.id,
                        }

                        # if kwargs['image_1920'] == False:
                        #     employee_id.sudo().write({
                        #         'image_1920':False
                        #     })
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "Employee Not Found!",
                            'id' : employee_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
                
            
        # return json.dumps(response)
        return response
    
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        if not request.env.user.employee_id:
            return request.redirect('/')
            # return super(EmployeePortalNew, self).home()
        # return request.redirect('/portals/me')
        return request.redirect('/portals')
    
    @route(['/portal/home'], type='http', auth="user", website=True)
    def portal(self, **kw):
        if not request.env.user.employee_id:
            return super(EmployeePortalNew, self).home()
        return request.redirect('/portals')
    

    @http.route(['/portal/home'], type='http', auth="user", website=True)
    def redirect_portal_home(self, **kw):
        return request.redirect('/portals')

# ---------------------------------------------------------------------------------------------------------------------------
    
    # ATTENDANCE
    @http.route([
        '/portals/hr_attendance/<string:action>',
        '/portals/hr_attendance/<string:action>/<int:active_id>'
    ], type="json", auth="user", method=['POST'], csrf=False)
    def attendance_crud(self, action, active_id=None, **kwargs):
        response = {
            'code': 99, 
            'status': 'error',
            'value': 'something went wrong!', 
        }
        if request.env.user.employee_id:
            values = kwargs.get('values')
            if action == 'create':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().create({
                        'employee_id': request.env.user.employee_id.id, #attendance[0].employee_id,
                        'attendance_type': values['attendance_type'],
                        'attendance_type_id': values['attendance_type_id'],
                        'partner_id': values['partner_id'] if values['partner_id'] != 0 else False,
                        'task': values['task'],
                        'description': values['description'],
                        'approver_id': values['approver_id'],
                        'pm_leader_id': values['pm_leader_id'],
                        'location_id': request.env.user.employee_id.work_location_id.id,
                        'type': 'attendance',
                        'check_in': False,
                        'check_out': False,
                    })

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully created the record!',
                        'id' : attendance_id.id,
                    }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
            
            if action == 'update':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    if attendance_id and attendance_id.state == 'draft':
                        values['check_in'] = False if values['check_in'] == '' else values['check_in']
                        values['check_out'] = False if values['check_out'] == '' else values['check_out']

                        tmpCekin = str(values['check_in']).replace('T', ' ') if values['check_in'] else False
                        tmpCekot = str(values['check_out']).replace('T', ' ') if values['check_out'] else False

                        tmpCekin = date_indonesia_save(parser.parse(tmpCekin)) if values['check_in'] else False #datetime.strptime(tmpCekin, "%Y-%m-%d %H:%M:%S")
                        tmpCekot = date_indonesia_save(parser.parse(tmpCekot)) if values['check_out'] else False #datetime.strptime(tmpCekot, "%Y-%m-%d %H:%M:%S")

                        if 'partner_id' in values:
                            values['partner_id'] = False if values['partner_id'] == 0 else values['partner_id']
                        values['check_in'] = tmpCekin #datetime.strptime(tmpCekin, "%Y-%m-%d %H:%M")
                        values['check_out'] = tmpCekot #datetime.strptime(tmpCekot, "%Y-%m-%d %H:%M")
                        attendance_id.sudo().write(values)

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : attendance_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only edit record that has 'To Submit' State!",
                            'id' : attendance_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
                            
            if action == 'delete':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    if attendance_id and attendance_id.state == 'draft' and not attendance_id.check_in:
                        attendance_id.sudo().unlink()

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully deleted the record!',
                            'id' : attendance_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only delete 'Draft' Attendance!" if attendance_id and attendance_id.state != 'draft' else 'Record not found!',
                            'id' : attendance_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'check_in':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    if attendance_id:
                        attendance_id.sudo().update({'check_in': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : attendance_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "Record not found!",
                            'id' : attendance_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'check_out':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    if attendance_id and attendance_id.check_in:
                        attendance_id.sudo().update({'check_out': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : attendance_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "Please Checkin First!",
                            'id' : attendance_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'approve':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    # if attendance_id and attendance_id.check_in:
                    attendance_id.sudo().write({
                        'state': 'approved',
                        'date_approve': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'approve_user_id': request.env.user.employee_id.user_id.id,
                        })
                    attendance_id.sudo().action_approve()

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully edited the record!',
                        'id' : attendance_id.id,
                    }
                    # else:
                    #     response = {
                    #         'code': 0, 
                    #         'status': 'failed',
                    #         'message': "Please Checkin First!",
                    #         'id' : attendance_id.id,
                    #     }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'reject':
                try:
                    attendance_id = request.env['hr.attendance'].sudo().browse(active_id)
                    # if attendance_id and attendance_id.check_in:
                    attendance_id.sudo().update({
                        'state': 'reject',
                        'date_reject': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'reject_user_id': request.env.user.employee_id.user_id.id,
                        'reject_reason': values['reject_reason'],
                        })

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully edited the record!',
                        'id' : attendance_id.id,
                    }
                    # else:
                    #     response = {
                    #         'code': 0, 
                    #         'status': 'failed',
                    #         'message': "Please Checkin First!",
                    #         'id' : attendance_id.id,
                    #     }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
            
            # if action == 'get_data_attendance_type':
            #     try:
            #         attendance_type = request.env['hr.attendance.type'].sudo().browse(active_id)
            #         response = {
            #             'code': 0, 
            #             'status': 'success',
            #             'message': 'You have successfully get the record!',
            #             'working_at_home' : attendance_type.working_at_home,
            #         }
            #     except Exception as e:
            #         print("errorr")
            #         print(e)
            #         request.env.cr.rollback()
            #         errmsg = str(e).replace('\"', '')
            #         response = {
            #             'code': 0, 
            #             'status': 'error',
            #             'id': active_id, 
            #             'value': 'something went wrong!', 
            #             'message': errmsg
            #         }
            
        # return json.dumps(response)
        return response

    # LIST ATTENDANCE
    @http.route('/portals/attendance', type='http', auth="user", method=['GET'])
    def render_portal_attendance(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Attendance',
            'description':'Welcome To Attendance',
            'attendance_type_list': request.env['hr.attendance.type'].sudo().search([('active','=',True),('regular','=',False)]),
            'attendance_list': request.env['hr.attendance'].sudo().search([('employee_id','=',request.env.user.employee_id.id)],limit=500, order="check_in desc"),
            'attendance_fields': request.env['hr.attendance'].sudo().fields_get(['employee_id','state','attendance_type']) #,['selection']
        }
        return env.get_template("attendance.html").render(data)

    @http.route('/portals/attendance_approve', type='http', auth="user", method=['GET'])
    def render_portal_attendance_approval(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Attendance to Approve',
            'description':'Welcome To Attendance',
            'attendance_type_list': request.env['hr.attendance.type'].sudo().web_search_read([('active','=',True),('regular','=',False)], ['id','name']),
            'attendance_list': request.env['hr.attendance'].sudo().search([
                ('approver_id','=',request.env.user.employee_id.id),
                ('state','=','draft')],
                limit=500, order="check_in desc"),
            'attendance_fields': request.env['hr.attendance'].sudo().fields_get(['employee_id','state','attendance_type']) #,['selection']
        }
        return env.get_template("attendance_approve.html").render(data)
    
    # CREATE ATTENDANCE
    @http.route('/portals/attendance/create', type='http', auth="user", method=['GET'])
    def render_portal_attendance_create(self, **kwargs):
        if not request.env.user.employee_id:
            return self._middleware_related_employee()
        
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Create New Attendance',
            'description':'Welcome To Attendance',
            'attendance_type_list': request.env['hr.attendance.type'].sudo().web_search_read([('active','=',True),('regular','=',False)], ['id','name']),
            'list_employee': request.env['hr.employee'].sudo().web_search_read([('id','=',request.env.user.employee_id.id)], ['id', 'name']),
            'list_partner': request.env['res.partner'].sudo().web_search_read([('customer_rank','>', 0)], ['id', 'name']),
            'list_approver': request.env['hr.employee'].sudo().web_search_read([
                ('is_approve_attendance','=',True),
                ], ['id', 'name']),
            'list_pm_leader': request.env['hr.employee'].sudo().web_search_read([
                ('is_responsible', '=', True),
                ], ['id', 'name']),
            'list_location': request.env['hr.expense.location'].sudo().web_search_read([], ['id', 'name']),
            'default_employee': request.env.user.employee_id
        }
        return env.get_template("attendance_create.html").render(data)

    # ATTENDANCE DETAIL/EDIT
    @http.route('/portals/attendance/<int:exp_id>', type='http', auth="user", method=['GET'])
    def render_portal_attendance_detail(self, exp_id, **kwargs):
        try:
            attendance = request.env['hr.attendance'].sudo().search([('id','=',exp_id)],limit=1)
            if attendance:
                data = {
                    'user': request.env.user.read(['id','name','share'])[0],
                    'title': "Attendance | "+ str(attendance[0].employee_id.name) + " " + attendance[0].attendance_type_id.name,
                    'description':'Welcome To Attendance',

                    'attendance': attendance[0],
                    'attendance_type_list': request.env['hr.attendance.type'].sudo().web_search_read([('active','=',True),('regular','=',False)], ['id','name']),
                    'list_employee': request.env['hr.employee'].sudo().web_search_read([('id','=',request.env.user.employee_id.id)], ['id', 'name']),
                    'list_partner': request.env['res.partner'].sudo().web_search_read([('customer_rank','>', 0)], ['id', 'name']),
                    'list_approver': request.env['hr.employee'].sudo().web_search_read([
                        ('is_approve_attendance','=',True),
                    ], ['id', 'name']),
                    'list_pm_leader': request.env['hr.employee'].sudo().web_search_read([
                        ('is_responsible', '=', True),
                        ], ['id', 'name']),
                    'list_location': request.env['hr.expense.location'].sudo().web_search_read([], ['id', 'name']),
                    'default_employee': request.env.user.employee_id
                }
                return env.get_template("attendance_detail.html").render(data)
            else:
                return request.redirect('/portals/attendance')
        except Exception as e:
            print("error get detail attendance")
            print(e)
            return request.redirect('/portals/attendance')
            # return request.render('http_routing.404')
        
    # ATTENDANCE APPROVE DETAIL/EDIT
    @http.route('/portals/attendance_approve/<int:exp_id>', type='http', auth="user", method=['GET'])
    def render_portal_attendance_approve_detail(self, exp_id, **kwargs):
        try:
            attendance = request.env['hr.attendance'].sudo().search([('id','=',exp_id)],limit=1)
            if attendance:
                data = {
                    'user': request.env.user.read(['id','name','share'])[0],
                    'title': "Attendance | "+ str(attendance[0].employee_id.name) + " " + attendance[0].attendance_type_id.name,
                    'description':'Welcome To Attendance Approve',

                    'attendance': attendance[0],
                    'attendance_type_list': request.env['hr.attendance.type'].sudo().web_search_read([('active','=',True),('regular','=',False)], ['id','name']),
                    'list_employee': request.env['hr.employee'].sudo().web_search_read([], ['id', 'name']),
                    'list_partner': request.env['res.partner'].sudo().web_search_read([('customer_rank','>', 0)], ['id', 'name']),
                    'list_approver': request.env['hr.employee'].sudo().web_search_read([], ['id', 'name']),
                    'list_pm_leader': request.env['hr.employee'].sudo().web_search_read([
                        ('id','!=',request.env.user.employee_id.id),
                        ('is_responsible', '=', True),
                        ], ['id', 'name']),
                    'list_location': request.env['hr.expense.location'].sudo().web_search_read([], ['id', 'name']),
                    'default_employee': request.env.user.employee_id
                }
                return env.get_template("attendance_detail_approve.html").render(data)
            else:
                return request.redirect('/portals/attendance_approve')
        except Exception as e:
            print("error get detail attendance")
            print(e)
            return request.redirect('/portals/attendance_approve')
            # return request.render('http_routing.404')
        
# ---------------------------------------------------------------------------------------------------------------------------
    
    # TIME OFF
    @http.route([
        '/portals/hr_leave/<string:action>',
        '/portals/hr_leave/<string:action>/<int:active_id>',
    ], type="json", auth="user", method=['POST'], csrf=False)
    def timeoff_crud(self, action, active_id=None, **kwargs):
        response = {
            'code': 99, 
            'status': 'error',
            'value': 'something went wrong!', 
        }
        if request.env.user.employee_id:
            values = kwargs.get('values')
            if action == 'create':
                try:
                    # import pprint
                    # pprint.pprint(values)
                    
                    leave_type = request.env['hr.leave.type'].sudo().search([('id','=',values['holiday_status_id'])])
                    if leave_type.request_unit == 'half_day':
                        request_unit_half = True
                        values['request_date_to'] = values['request_date_from']

                        if values['request_date_from_period'] == 'am':
                            tmpFrom = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                            tmpFrom = datetime(tmpFrom.year, tmpFrom.month, tmpFrom.day, 1, 0)
                            values['date_from'] = tmpFrom.strftime("%Y-%m-%d %H:%M:%S")

                            tmpTo = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                            tmpTo = datetime(tmpTo.year, tmpTo.month, tmpTo.day, 5, 0)
                            values['date_to'] = tmpTo.strftime("%Y-%m-%d %H:%M:%S")
                        elif values['request_date_from_period'] == 'pm':
                            tmpFrom = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                            tmpFrom = datetime(tmpFrom.year, tmpFrom.month, tmpFrom.day, 6, 0)
                            values['date_from'] = tmpFrom.strftime("%Y-%m-%d %H:%M:%S")

                            tmpTo = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                            tmpTo = datetime(tmpTo.year, tmpTo.month, tmpTo.day, 10, 0)
                            values['date_to'] = tmpTo.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        request_unit_half = False
                        values['request_date_from_period'] = ''

                        tmpFrom = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                        tmpFrom = datetime(tmpFrom.year, tmpFrom.month, tmpFrom.day, 1, 0)
                        values['date_from'] = tmpFrom.strftime("%Y-%m-%d %H:%M:%S")

                        tmpTo = datetime.strptime(values['request_date_to'], "%Y-%m-%d")
                        tmpTo = datetime(tmpTo.year, tmpTo.month, tmpTo.day, 10, 0)
                        values['date_to'] = tmpTo.strftime("%Y-%m-%d %H:%M:%S")
                    
                    vals = {
                        'employee_id': request.env.user.employee_id.id, 
                        'name': values['name'],
                        'holiday_status_id': values['holiday_status_id'],
                        'request_date_from': values['request_date_from'],
                        'request_date_to': values['request_date_to'],
                        'holiday_type': 'employee',
                        'request_date_from_period': values['request_date_from_period'],
                        'employee_ids': [[6, False, [request.env.user.employee_id.id]]],
                        'department_id': request.env.user.employee_id.department_id.id,
                        # datetime.datetime(2018, 6, 1)
                        'date_from': values['date_from'],
                        'date_to': values['date_to'],
                        'manager_id': request.env.user.employee_id.parent_id.id,
                        'approver_id': values['approver_id'],
                        'pm_leader_id': values['pm_leader_id'],
                        'request_unit_half': request_unit_half,
                    }

                    # pprint.pprint("------------------------------")
                    # pprint.pprint(vals)

                    timeoff_id = request.env['hr.leave'].sudo().create(vals)
                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully created the record!',
                        'id' : timeoff_id.id,
                    }

                    if kwargs['documents']:
                        attachment_ids = self._handle_attachments(active_model='hr.leave', active_id=timeoff_id.id, documents=kwargs['documents'])
                        response['attachment_ids'] = attachment_ids

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
            
            if action == 'update':
                try:
                    # import pprint
                    # pprint.pprint(values)

                    timeoff_id = request.env['hr.leave'].sudo().browse(active_id)
                    if timeoff_id and timeoff_id.state in ['draft','confirm']:
                        leave_type = request.env['hr.leave.type'].sudo().search([('id','=',values['holiday_status_id'])])
                        if leave_type.request_unit == 'half_day':
                            values['request_unit_half'] = True
                            values['request_date_to'] = values['request_date_from']

                            if values['request_date_from_period'] == 'am':
                                tmpFrom = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                                tmpFrom = datetime(tmpFrom.year, tmpFrom.month, tmpFrom.day, 1, 0)
                                values['date_from'] = tmpFrom.strftime("%Y-%m-%d %H:%M:%S")

                                tmpTo = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                                tmpTo = datetime(tmpTo.year, tmpTo.month, tmpTo.day, 5, 0)
                                values['date_to'] = tmpTo.strftime("%Y-%m-%d %H:%M:%S")
                            elif values['request_date_from_period'] == 'pm':
                                tmpFrom = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                                tmpFrom = datetime(tmpFrom.year, tmpFrom.month, tmpFrom.day, 6, 0)
                                values['date_from'] = tmpFrom.strftime("%Y-%m-%d %H:%M:%S")

                                tmpTo = datetime.strptime(values['request_date_from'], "%Y-%m-%d")
                                tmpTo = datetime(tmpTo.year, tmpTo.month, tmpTo.day, 10, 0)
                                values['date_to'] = tmpTo.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            values['request_unit_half'] = False

                        tmpDateFrom = str(values['request_date_from']).replace('T', ' ')
                        tmpDateTo = str(values['request_date_to']).replace('T', ' ') 
                        values['request_date_from'] = tmpDateFrom #datetime.strptime(tmpCekin, "%Y-%m-%d %H:%M")
                        values['request_date_to'] = tmpDateTo #datetime.strptime(tmpCekot, "%Y-%m-%d %H:%M")

                        # pprint.pprint("------------------------------")
                        # pprint.pprint(values)

                        timeoff_id.sudo().update(values)

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully edited the record!',
                            'id' : timeoff_id.id,
                        }

                        if kwargs['documents']:
                            attachment_ids = self._handle_attachments(active_model='hr.leave', active_id=timeoff_id.id, documents=kwargs['documents'])
                            response['attachment_ids'] = attachment_ids
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only edit record that has 'To Approve' State!",
                            'id' : timeoff_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
                            
            if action == 'get_type_holiday':
                try:
                    holiday_type = request.env['hr.leave.type'].sudo().browse(active_id)
                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully edited the record!',
                        'type' : holiday_type.request_unit,
                        'support_document': holiday_type.support_document,
                    }
                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'delete':
                try:
                    timeoff_id = request.env['hr.leave'].sudo().browse(active_id)
                    if timeoff_id and timeoff_id.state in ['draft','confirm']:
                        timeoff_id.sudo().unlink()

                        response = {
                            'code': 0, 
                            'status': 'success',
                            'message': 'You have successfully deleted the record!',
                            'id' : timeoff_id.id,
                        }
                    else:
                        response = {
                            'code': 0, 
                            'status': 'failed',
                            'message': "You can only delete 'To Approve' Leave!" if timeoff_id and timeoff_id.state not in ['draft','confirm'] else 'Record not found!',
                            'id' : timeoff_id.id,
                        }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'approve':
                try:
                    leave_id = request.env['hr.leave'].sudo().browse(active_id)
                    leave_id.sudo().update({
                        'date_approve': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'approve_user_id': request.env.user.employee_id.user_id.id,
                        })
                    leave_id.sudo().action_approve()

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully edited the record!',
                        'id' : leave_id.id,
                    }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }

            if action == 'reject':
                try:
                    leave_id = request.env['hr.leave'].sudo().browse(active_id)
                    leave_id.sudo().update({
                        'date_reject': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'reject_user_id': request.env.user.employee_id.user_id.id,
                        'reject_reason': values['reject_reason'],
                        })
                    leave_id.sudo().action_refuse()

                    response = {
                        'code': 0, 
                        'status': 'success',
                        'message': 'You have successfully edited the record!',
                        'id' : leave_id.id,
                    }

                except Exception as e:
                    print("errorr")
                    print(e)
                    request.env.cr.rollback()
                    errmsg = str(e).replace('\"', '')
                    response = {
                        'code': 0, 
                        'status': 'error',
                        'id': active_id, 
                        'value': 'something went wrong!', 
                        'message': errmsg
                    }
            
        # return json.dumps(response)
        return response

    # CREATE TIME OFF
    @http.route('/portals/time-off/create', type='http', auth="user", method=['GET'])
    def render_portal_timeoff_create(self, **kwargs):
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            # 'title': 'Create New Time Off (Used ' + str(round(request.env.user.employee_id.allocation_count - request.env.user.employee_id.allocation_used_count))  + ' of ' + str(round(request.env.user.employee_id.allocation_count)) + ')' ,
            'title': 'Create New Time Off (' + str(request.env.user.employee_id.allocation_used_display)  + ' of ' + str(request.env.user.employee_id.allocation_display) + ' Days Allocation Leave)' ,
            'description':'Welcome To Time Off',
            'list_employee': request.env['hr.employee'].sudo().web_search_read([('id','=',request.env.user.employee_id.id)], ['id', 'name']),
            'list_time_off_type': request.env['hr.leave.type'].sudo().web_search_read(
                ['|', ('requires_allocation','=','no'), ('has_valid_allocation','=', True)], ['id', 'name']),
            'list_approver': request.env['hr.employee'].sudo().web_search_read([
                ('is_approve_attendance','=',True),
                ], ['id', 'name']),
            'list_pm_leader': request.env['hr.employee'].sudo().web_search_read([
                ('is_responsible', '=', True),
                ], ['id', 'name']),
            'default_employee': request.env.user.employee_id
        }
        return env.get_template("time_off_create.html").render(data)

    @http.route('/portals/time-off/<string:action>/<int:exp_id>', type='http', auth="user", method=['GET'])
    def render_portal_timeoff_detail(self, action, exp_id, **kwargs):
        try:
            timeoff = request.env['hr.leave'].sudo().search([('id','=',exp_id)],limit=1)
            if timeoff:
                title = ""
                list_type = []

                timeoff_attachments = request.env['ir.attachment'].sudo().search([('res_id', '=', timeoff[0].id), ('res_model', '=', 'hr.leave')]).read(['id', 'name','website_url','file_size'])

                if action == 'user':
                    title = "Time-Off (" + str(request.env.user.employee_id.allocation_used_display)  + "/" + str(request.env.user.employee_id.allocation_display) + " Days) | "+ str(timeoff[0].employee_id.name) + " | " + timeoff[0].holiday_status_id.name + " | " + timeoff[0].duration_display
                    list_type = request.env['hr.leave.type'].sudo().web_search_read(
                        ['|', ('requires_allocation','=','no'), ('has_valid_allocation','=', True)], ['id', 'name'])
                elif action == 'approve':
                    title = "Time-Off Approve ( " + str(timeoff[0].employee_id.name) + " | " + timeoff[0].holiday_status_id.name + " | " + timeoff[0].duration_display + ")"
                    list_type = request.env['hr.leave.type'].sudo().web_search_read([], ['id', 'name'])
                data = {
                    'user': request.env.user.read(['id','name','share'])[0],
                    'title': title,
                    'description':'Welcome To Time Off',
                    'timeoff': timeoff[0],
                    'list_employee': request.env['hr.employee'].sudo().web_search_read([('id','=',request.env.user.employee_id.id)], ['id', 'name']),
                    'list_time_off_type': list_type,
                    'list_approver': request.env['hr.employee'].sudo().web_search_read([
                        ('is_approve_attendance','=',True),
                        ], ['id', 'name']),
                    'list_pm_leader': request.env['hr.employee'].sudo().web_search_read([
                        ('is_responsible', '=', True),
                        ], ['id', 'name']),
                    'timeoff_attachments':timeoff_attachments,
                    'default_employee': request.env.user.employee_id
                }
                if action == 'user':
                    return env.get_template("time_off_detail.html").render(data)
                elif action == 'approve':
                    return env.get_template("time_off_detail_approve.html").render(data)
            else:
                if action == 'user':
                    return request.redirect('/portals/time-off')
                elif action == 'approve':
                    return request.redirect('/portals/time-off_approve')
        except Exception as e:
            print("error get detail time-off")
            print(e)
            return request.redirect('/portals/time-off')
            # return request.render('http_routing.404')

    # LIST TIME OFF
    @http.route('/portals/time-off', type='http', auth="user", method=['GET'])
    def render_portal_timeoff(self, **kwargs):
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Time-Off (' + str(request.env.user.employee_id.allocation_used_display)  + '/' + str(request.env.user.employee_id.allocation_display) + ' Days)' ,
            'description':'Welcome To Time-Off',
            'timeoff_list': request.env['hr.leave'].sudo().search([('employee_id','=',request.env.user.employee_id.id)],limit=500, order="request_date_from desc"),
            'timeoff_fields': request.env['hr.leave'].sudo().fields_get(['employee_id','holiday_status_id','state']) #,['selection']
        }
        return env.get_template("time_off.html").render(data)
    
# ---------------------------------------------------------------------------------------------------------------------------
    
    # LIST TIME OFF APPROVAL
    @http.route('/portals/time-off_approve', type='http', auth="user", method=['GET'])
    def render_portal_timeoff_approve(self, **kwargs):
        data = {
            'user':request.env.user.read(['id','name','share'])[0],
            'title': 'Time-Off Approve',
            'description':'Welcome To Time-Off',
            'timeoff_list': request.env['hr.leave'].sudo().search([
                ('approver_id','=',request.env.user.employee_id.id),
                ('state','in',['confirm','draft'])
                ],limit=500, order="request_date_from desc"),
            'timeoff_fields': request.env['hr.leave'].sudo().fields_get(['employee_id','holiday_status_id','state']) #,['selection']
        }
        return env.get_template("time_off_approve.html").render(data)