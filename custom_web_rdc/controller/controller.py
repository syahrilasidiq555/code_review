# -*- coding: utf-8 -*-
import jinja2
import json
import base64
import os

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from babel.dates import format_date, format_datetime, format_time

import odoo
from odoo import http, models, fields, _
from odoo.http import request, route
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
# def remove_b64(text):
#     return str(text)[2:-1]

# def get_dict(text):
#     return dict(text)

# if hasattr(sys, 'frozen'):
#     # When running on compiled windows binary, we don't have access to package loader.
#     path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
#     loader = jinja2.FileSystemLoader(path)
# else:
#     loader = jinja2.PackageLoader('odoo.addons.web', "views")

path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'template_views'))
loader = jinja2.FileSystemLoader(path)

env = jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps
# env.filters['remove_b64'] = remove_b64
# env.filters['dict'] = get_dict
env.filters['json_load'] = json.loads



AVAILABLE_MODELS = ['res.partner']
AVAILABLE_FIELDS = {
    'res.partner': ['name','street','city','state_id','country_id','phone','email','is_jenazah'],
}


class WebsitePortalControllerRDC(http.Controller):
    #######################################################################
    # REDIRECT
    #######################################################################

    # Main Page
    @route(['/'], type='http', auth="public", website=True)
    def redirect_home(self, **kw):
        # return request.redirect('/home')
        return self.render_portal_home()
    
    @route(['/contactus'], type='http', auth="public", website=True)
    def redirect_contactus_page(self, **kw):
        return request.redirect('/')

    def render_portal_home(self, **kwargs):
        data = {
            'user':request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None,
            'title': 'Rumah Duka Carolus',
            'description':'Welcome To RDC',
            # 'menus':menus
        }
        return env.get_template("index.html").render(data)
    

    #######################################################################
    # AUTH
    #######################################################################
    
    # LOGIN PAGE
    @http.route('/web/login', type='http', auth="public")
    def render_login_page(self, **kwargs):
        data = {
            'user': None,
            'title': 'Login',
            'description':'Login',
            'csrf_token':request.csrf_token(),
            'error': None,
        }

        if request.httprequest.method == 'GET':
            user = request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None
            if user:
                data['user'] = user
                return request.redirect('/')
            return env.get_template("login.html").render(data)
        
        elif request.httprequest.method == 'POST':
            try:
                request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                return request.redirect('/')
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    data['error'] = _("Wrong login/password")
                else:
                    data['error'] = e.args[0]
            except Exception as e:
                data['error'] = str(e)
            return env.get_template("login.html").render(data)

    # RESET PASSWORD PAGE
    @http.route('/web/reset_password', type='http', auth="public")
    def render_reset_password_page(self, **kwargs):
        data = {
            'user': None,
            'title': 'Reset Password',
            'description':'Reset Passwod',
            'csrf_token':request.csrf_token(),
            'error': None,
        }

        if request.httprequest.method == 'GET':
            user = request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None
            if user:
                data['user'] = user
                return request.redirect('/')
            return env.get_template("reset-password.html").render(data)
        
        elif request.httprequest.method == 'POST':
            try:
                login = request.params['login']
                request.env['res.users'].sudo().reset_password(login)
                data['error'] = _("An email has been sent with credentials to reset your password")
            except UserError as e:
                data['error'] = e.args[0]
            except SignupError:
                data['error'] = _("Could not reset your password")
            except Exception as e:
                data['error'] = str(e)
            
            return env.get_template("reset-password.html").render(data)


    #######################################################################
    # NEW PAGE
    #######################################################################

    # CUSTOMER FORM PAGE
    @http.route('/customer-form/<token>', type='http', auth="public")
    def render_customer_form_page(self, token, **kwargs):
        cust_form = request.env['customer.form.website'].sudo().search([('token','=',token),('status','=','belum_diisi')])
        data = {
            'user':request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None,
            'title': 'Customer Form',
            'description':'Customer Form',
            'csrf_token':request.csrf_token(),
            'error': None,
        }
        if request.httprequest.method == 'GET':
            if cust_form:
                data['data'] = cust_form
                data['provinces'] = request.env['res.country.state'].sudo().web_search_read([], ['id', 'name'])

                return env.get_template("customer-form.html").render(data)
            else:
                return request.redirect('/')
        if request.httprequest.method == 'POST':
            fields_list = ['name','email','phone','document']
            # validating input
            error_validate = False
            # for field in fields_list:
            #     if not request.params.get(field):
            #         error_validate = True
            #         data['error'] = 'field {field} must be filled'.format(
            #             field=field
            #         )
            if cust_form and not error_validate:
                partner_obj = request.env['res.partner']


                # create customer
                cust_values = {}
                cust_values['name'] = request.params['customer_name'] if request.params.get('customer_name') else None
                cust_values['email'] = request.params['customer_email'] if request.params.get('customer_email') else None
                cust_values['phone'] = request.params['customer_phone'] if request.params.get('customer_phone') else None
                cust_values['vat'] = request.params['customer_ktp'] if request.params.get('customer_ktp') else None
                cust_values['street'] = request.params['customer_street'] if request.params.get('customer_street') else None
                cust_values['zip'] = request.params['customer_zip'] if request.params.get('customer_zip') else None
                cust_values['city'] = request.params['customer_city'] if request.params.get('customer_city') else None
                cust_values['state_id'] = int(request.params['customer_province']) if request.params.get('customer_province') else None
                customer = partner_obj.sudo().create(cust_values)
                
                
                # create jenazah
                jnz_values = {}
                jnz_values['name'] = request.params['jenazah_name'] if request.params.get('jenazah_name') else None
                jnz_values['email'] = request.params['jenazah_email'] if request.params.get('jenazah_email') else None
                jnz_values['phone'] = request.params['jenazah_phone'] if request.params.get('jenazah_phone') else None
                jnz_values['is_jenazah'] = True
                jnz_values['parent_id'] = customer.id
                jenazah = partner_obj.sudo().create(jnz_values)
                jenazah.vat = request.params['jenazah_ktp'] if request.params.get('jenazah_ktp') else None
                jenazah.street = request.params['jenazah_street'] if request.params.get('jenazah_street') else None
                jenazah.zip = request.params['jenazah_zip'] if request.params.get('jenazah_zip') else None
                jenazah.city = request.params['jenazah_city'] if request.params.get('jenazah_city') else None
                jenazah.state_id = int(request.params['jenazah_province']) if request.params.get('jenazah_province') else None

                # insert to customer_form
                cust_form.customer_id = customer.id
                cust_form.jenazah_id = jenazah.id
                cust_form.status = 'sudah_diisi'
                cust_form.date = datetime.now().date()

                ############
                # create file
                ############
                attachment_list = []
                file = request.params['documentA']
                attachment_id = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(file.read()),
                    'res_model': 'customer.form.website',
                    'res_id': cust_form.id
                })
                attachment_list.append((4,attachment_id.id))

                file = request.params['documentB']
                attachment_id = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(file.read()),
                    'res_model': 'customer.form.website',
                    'res_id': cust_form.id
                })
                attachment_list.append((4,attachment_id.id))

                file = request.params['documentC']
                attachment_id = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(file.read()),
                    'res_model': 'customer.form.website',
                    'res_id': cust_form.id
                })
                attachment_list.append((4,attachment_id.id))


                cust_form.file_attachments = attachment_list

                data['record'] = cust_form
            else:
                data['error'] = 'token not available or invalid!'

            return env.get_template("customer-form-finished.html").render(data)


    @http.route('/dashboard/acara', type='http', auth="user")
    def render_customer_form_page(self, **kwargs):
        # categ_ruangdoa = request.env.ref('custom_sale_order.categ_ruangdoa')
        # rental_schedule = request.env['sale.rental.schedule'].search([('product_id.categ_id','=',categ_ruangdoa.id)],limit=500, order="pickup_date desc")
        # acara = request.env['customer.form.website'].search([('jenazah_id','!=',False)], offset=0,limit=10, order="create_date desc")
        data = {
            'user':request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None,
            'title': 'Dashboard Acara',
            'description':'Welcome To Dashboard RDC',
            # 'datas': acara,
            # 'csrf_token':request.csrf_token(),
            # 'error': None,
        }
        if request.httprequest.method == 'GET':
            return env.get_template("dashboard/acara.html").render(data)
        

    @http.route('/dashboard/columbarium', type='http', auth="user")
    def render_dashboard_columbarium(self, **kwargs):
        # categ_ruangdoa = request.env.ref('custom_sale_order.categ_ruangdoa')
        # rental_schedule = request.env['sale.rental.schedule'].search([('product_id.categ_id','=',categ_ruangdoa.id)],limit=500, order="pickup_date desc")
        # acara = request.env['customer.form.website'].search([('jenazah_id','!=',False)], offset=0,limit=10, order="create_date desc")
        data = {
            'user':request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None,
            'title': 'Dashboard Columbarium',
            'description':'Welcome To Dashboard RDC',
            # 'datas': acara,
            # 'csrf_token':request.csrf_token(),
            # 'error': None,
        }
        if request.httprequest.method == 'GET':
            return env.get_template("dashboard/columbarium.html").render(data)


    @http.route([
        '/api/rdc/get/data_acara',
    ], type="json", auth="user", method=['POST'], csrf=False)
    def get_data_acara(self, **kwargs):
        response = {}
        try:
            records = request.env['customer.form.website'].search([('jenazah_id','!=',False)], offset=kwargs.get('offset') or 0, limit=kwargs.get('limit') or 10, order="create_date desc")
            if records:
                datas = map(lambda x : {
                    "id" : x.id,
                    "jenazah" : x.jenazah_id.name,
                    "ruangan" : x.sale_order_id.ruang_semayam_id.display_name or "",
                    "kegiatan" : x.almarhum_tujuan or "",
                    "tujuan": x.tujuan_string or ""
                }, records)
                response = {
                    'code': 0, 
                    'status': 'success',
                    'message': 'You have successfully get the record!',
                    'datas' : list(datas),
                }
            else:
                response = {
                    'code': 0, 
                    'status': 'failed',
                    'message': 'No record available!',
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
    
    @http.route([
        '/api/rdc/get/data_acara_columbarium',
    ], type="json", auth="user", method=['POST'], csrf=False)
    def get_data_acara_columbarium(self, **kwargs):
        response = {}
        try:
            records = request.env['customer.form.website'].search([('jenazah_id','!=',False)], offset=kwargs.get('offset') or 0, limit=kwargs.get('limit') or 10, order="create_date desc")
            if records:
                datas = map(lambda x : {
                    "id" : x.id,
                    "jenazah" : x.jenazah_id.name,
                    "ruangan" : x.sale_order_id.ruang_semayam_id.display_name or "",
                    "kegiatan" : x.kegiatan_string or "",
                    "hari_string": x.hari_string or "",
                    "waktu_pelaksanaan_string": x.waktu_pelaksanaan_string or "",
                }, records)
                response = {
                    'code': 0, 
                    'status': 'success',
                    'message': 'You have successfully get the record!',
                    'datas' : list(datas),
                }
            else:
                response = {
                    'code': 0, 
                    'status': 'failed',
                    'message': 'No record available!',
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
    

    @http.route('/dashboard/semayam', type='http', auth="user")
    def render_customer_form_for_semayam_page(self, **kwargs):
        # categ_ruangdoa = request.env.ref('custom_sale_order.categ_ruangdoa')
        # rental_schedule = request.env['sale.rental.schedule'].search([('product_id.categ_id','=',categ_ruangdoa.id)],limit=500, order="pickup_date desc")
        # acara = request.env['customer.form.website'].search([('jenazah_id','!=',False)], offset=0,limit=10, order="create_date desc")
        data = {
            'user':request.env.user.read(['id','name','share'])[0] if request.env.user.id != 4 else None,
            'title': 'Dashboard Semayam',
            'description':'Dashboard Semayam',
            # 'datas': acara,
            # 'csrf_token':request.csrf_token(),
            # 'error': None,
        }
        if request.httprequest.method == 'GET':
            return env.get_template("dashboard/semayam.html").render(data)
        
    @http.route([
        '/api/rdc/get/data_lokasi_product',
    ], type="json", auth="user", method=['POST'], csrf=False)
    def get_data_lokasi_product(self, **kwargs):
        response = {}
        datas = []
        try:
            # get data product by lokasi
            categ_ruang_semayam = request.env.ref('custom_sale_order.categ_ruang_semayam')
            record_products = request.env['product.product'].search([('active','=',True),('categ_id','=',categ_ruang_semayam.id)], 
                                                                    offset=kwargs.get('offset') or 0, limit=kwargs.get('limit') or 10, 
                                                                    order="display_name asc, product_location_id asc")
            record_rents = request.env['sale.rental.report'].search([('date','=',datetime.now().date()),('product_id.categ_id','=',categ_ruang_semayam.id)])
            if record_products:
                datas = map(lambda x : {
                    "id" : x.id,
                    "name" : x.name,
                    "active" : x.active,
                    "product" : list(map(lambda y : {
                        "id": y.id,
                        "name": y.display_name,
                        "rent": list(map(lambda z : {
                            "alm_name": z.order_id.partner_id.name,
                            "date": z.date, 
                            "ket_kremasi": "KREMATORIUM RUMAH DUKA CAROLUS, TGL " + str((z.order_id.customer_form_id.almarhum_jadwal_kremasi + timedelta(hours=7)).strftime("%d %b %Y PKL %H:%M")) if z.order_id.customer_form_id.almarhum_tujuan == 'kremasi' else '',
                            "ket_makam": "MAKAM : " + z.order_id.customer_form_id.almarhum_jabodetabek_pemakaman_id.name + ", TGL : " + str((z.order_id.customer_form_id.almarhum_tanggal_pemakaman + timedelta(hours=7)).strftime("%d %b %Y PKL %H:%M")) if z.order_id.customer_form_id.almarhum_tujuan == 'pemakaman' else '',
                        }, record_rents.filtered(lambda z1: z1.product_id.id == y.id))) #if record_rents.filtered(lambda z1: z1.product_id.id == y.id) else [{"alm_name":"Available","date": ""}]
                    }, record_products.filtered(lambda y1: y1.product_location_id.id == x.id))),
                }, record_products.mapped('product_location_id'))

                response = {
                    'code': 0, 
                    'status': 'success',
                    'message': 'You have successfully get the record!',
                    'datas' : list(datas),
                }
            else:
                response = {
                    'code': 0, 
                    'status': 'failed',
                    'message': 'No record available!',
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
        # print(response)
        return response

    # # CRUD BACKEND (WILL BE MODIFIED SOON)
    # @http.route([
    #     '/api/rdc/<model>/<string:action>',
    #     '/api/rdc/<model>/<string:action>/<int:active_id>'
    # ], type="json", auth="user", method=['POST'], csrf=False)
    # def expense_crud(self, model, action, active_id=None, **kwargs):
    #     available_models = AVAILABLE_MODELS
    #     available_fields = AVAILABLE_FIELDS
    
    #     token = kwargs.get('token')
    #     values = kwargs.get('values')

    #     response = {
    #         'code': 99, 
    #         'status': 'error',
    #         'value': 'something went wrong!', 
    #     }

    #     # check if model is available
    #     if model not in available_models:
    #         response['value'] = 'Token or Model is not available!'
    #         return response

    #     values = kwargs.get('values')
        
    #     # filter field values hanya berdasarkan available field
    #     values_filtered = {}
    #     for field in available_fields[model]:
    #         if values.get(field):
    #             values_filtered[field] = values[field]
        
    #     if action == 'search':
    #         try:
    #             record = request.env[model].sudo().search(domain=values.get('domain') or [], offset=values.get('offset') or None, limit=values.get('limit') or None)
    #             response = {
    #                 'code': 0, 
    #                 'status': 'success',
    #                 'message': 'You have successfully get the records!',
    #                 'id' : record.id,
    #             }

    #         except Exception as e:
    #             print("errorr")
    #             print(e)
    #             request.env.cr.rollback()
    #             errmsg = str(e).replace('\"', '')
    #             response = {
    #                 'code': 0, 
    #                 'status': 'error',
    #                 'value': 'something went wrong!', 
    #                 'message': errmsg
    #             }

    #     if action == 'create':
    #         try:
    #             record = request.env[model].sudo().create(values_filtered)
    #             response = {
    #                 'code': 0, 
    #                 'status': 'success',
    #                 'message': 'You have successfully created the record!',
    #                 'id' : record.id,
    #             }

    #         except Exception as e:
    #             print("errorr")
    #             print(e)
    #             request.env.cr.rollback()
    #             errmsg = str(e).replace('\"', '')
    #             response = {
    #                 'code': 0, 
    #                 'status': 'error',
    #                 'value': 'something went wrong!', 
    #                 'message': errmsg
    #             }

        
    #     if action == 'update':
    #         try:
    #             record = request.env[model].sudo().browse(active_id)
    #             record.sudo().update(values_filtered)
    #             response = {
    #                 'code': 0, 
    #                 'status': 'success',
    #                 'message': 'You have successfully edited the record!',
    #                 'id' : record.id,
    #             }

    #         except Exception as e:
    #             print("errorr")
    #             print(e)
    #             request.env.cr.rollback()
    #             errmsg = str(e).replace('\"', '')
    #             response = {
    #                 'code': 0, 
    #                 'status': 'error',
    #                 'id': active_id, 
    #                 'value': 'something went wrong!', 
    #                 'message': errmsg
    #             }
            
        
    #     if action == 'delete':
    #             try:
    #                 record = request.env[model].sudo().browse(active_id)
    #                 record.sudo().unlink()

    #                 response = {
    #                     'code': 0, 
    #                     'status': 'success',
    #                     'message': 'You have successfully deleted the record!',
    #                     'id' : record.id,
    #                 }

    #             except Exception as e:
    #                 print("errorr")
    #                 print(e)
    #                 request.env.cr.rollback()
    #                 errmsg = str(e).replace('\"', '')
    #                 response = {
    #                     'code': 0, 
    #                     'status': 'error',
    #                     'id': active_id, 
    #                     'value': 'something went wrong!', 
    #                     'message': errmsg
    #                 }

    #     # return json.dumps(response)
    #     return response
