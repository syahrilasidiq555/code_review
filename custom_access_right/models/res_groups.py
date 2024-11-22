from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import decorator
import passlib.context
import pytz
from lxml import etree
from lxml.builder import E

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.modules.module import get_module_resource
from odoo.osv import expression
from odoo.service.db import check_super
from odoo.tools import partition, collections, frozendict, lazy_property, image_process

#
# Functions for manipulating boolean and selection pseudo-fields
#
def name_boolean_group(id):
    return 'in_group_' + str(id)

def name_selection_groups(ids):
    return 'sel_groups_' + '_'.join(str(it) for it in sorted(ids))

def is_boolean_group(name):
    return name.startswith('in_group_')

def is_selection_groups(name):
    return name.startswith('sel_groups_')

def is_reified_group(name):
    return is_boolean_group(name) or is_selection_groups(name)

def get_boolean_group(name):
    return int(name[9:])

def get_selection_groups(name):
    return [int(v) for v in name[11:].split('_')]

class ResGroups(models.Model):
    _inherit = "res.groups"
    _order = 'sequence asc, name'

    sequence = fields.Integer(string='Sequence', default=10, tracking=True)

    @api.constrains('users')
    def _constrains_users_add(self):
        for record in self:
            not_allowed_groups = eval(self.env['ir.config_parameter'].sudo().get_param('custom_access_right.not_allowed_groups_ids')) if self.env['ir.config_parameter'].sudo().get_param('custom_access_right.not_allowed_groups_ids') else []
            
            if not_allowed_groups and self.env.user.id in record.users.ids:
                if not self.env.user.has_group("base.group_system") and record.id in not_allowed_groups:
                    message = "Hanya user dengan access group Administrasi / Pengaturan yang dapat menambahkan anda ke group yang ada di list sebagai berikut : \n\n"
                    
                    grouplist = self.env['res.groups'].search([('id','in',not_allowed_groups)])
                    for group in grouplist:
                        message += "- %s \n" % group.display_name

                    raise ValidationError(message)

    # @api.model
    # def _update_user_groups_view(self):
    #     """ Modify the view with xmlid ``base.user_groups_view``, which inherits
    #         the user form view, and introduces the reified group fields.
    #     """
    #     # remove the language to avoid translations, it will be handled at the view level
    #     self = self.with_context(lang=None)

    #     # We have to try-catch this, because at first init the view does not
    #     # exist but we are already creating some basic groups.
    #     view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
    #     if not (view and view.exists() and view._name == 'ir.ui.view'):
    #         return

    #     if self._context.get('install_filename') or self._context.get(MODULE_UNINSTALL_FLAG):
    #         # use a dummy view during install/upgrade/uninstall
    #         xml = E.field(name="groups_id", position="after")

    #     else:
    #         group_no_one = view.env.ref('base.group_no_one')
    #         group_employee = view.env.ref('base.group_user')
    #         xml1, xml2, xml3 = [], [], []
    #         xml_by_category = {}
    #         xml1.append(E.separator(string='User Type', colspan="2", groups='base.group_no_one'))

    #         user_type_field_name = ''
    #         user_type_readonly = str({})
    #         sorted_tuples = sorted(self.get_groups_by_application(),
    #                                key=lambda t: t[0].xml_id != 'base.module_category_user_type')
    #         for app, kind, gs, category_name in sorted_tuples:  # we process the user type first
    #             attrs = {}
    #             # hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
    #             if app.xml_id in self._get_hidden_extra_categories():
    #                 attrs['groups'] = 'base.group_no_one'

    #             # User type (employee, portal or public) is a separated group. This is the only 'selection'
    #             # group of res.groups without implied groups (with each other).
    #             if app.xml_id == 'base.module_category_user_type':
    #                 # application name with a selection field
    #                 field_name = name_selection_groups(gs.ids)
    #                 user_type_field_name = field_name
    #                 user_type_readonly = str({'readonly': [(user_type_field_name, '!=', group_employee.id)]})
    #                 attrs['widget'] = 'radio'
    #                 attrs['groups'] = 'base.group_no_one'
    #                 xml1.append(E.field(name=field_name, **attrs))
    #                 xml1.append(E.newline())

    #             elif kind == 'selection':
    #                 # application name with a selection field
    #                 field_name = name_selection_groups(gs.ids)
    #                 attrs['attrs'] = user_type_readonly
    #                 if category_name not in xml_by_category:
    #                     xml_by_category[category_name] = []
    #                     xml_by_category[category_name].append(E.newline())
    #                 xml_by_category[category_name].append(E.field(name=field_name, **attrs))
    #                 xml_by_category[category_name].append(E.newline())

    #             else:
    #                 # application separator with boolean fields
    #                 app_name = app.name or 'Other'
    #                 # xml3.append(E.h3(string=app_name, colspan="4", **attrs))
    #                 xml3.append(E.h3(E.u(E.span(app_name)), colspan="4", style="background-color: #e8e6eb;"))
    #                 # <h2 colspan="4" style="background-color: #e8e6eb;"><u><span>Custom Record Rule</span></u></h2>

    #                 attrs['attrs'] = user_type_readonly
    #                 for g in gs:
    #                     field_name = name_boolean_group(g.id)
    #                     if g == group_no_one:
    #                         # make the group_no_one invisible in the form view
    #                         xml3.append(E.field(name=field_name, invisible="1", **attrs))
    #                     else:
    #                         xml3.append(E.field(name=field_name, widget="boolean_toggle", **attrs))

    #         xml3.append({'class': "o_label_nowrap"})
    #         if user_type_field_name:
    #             user_type_attrs = {'invisible': [(user_type_field_name, '!=', group_employee.id)]}
    #         else:
    #             user_type_attrs = {}

    #         for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
    #             master_category_name = xml_cat[1]
    #             xml2.append(E.group(*(xml_by_category[xml_cat]), col="2", string=master_category_name))

    #         xml = E.field(
    #             E.group(*(xml1), col="2"),
    #             E.group(*(xml2), col="2", attrs=str(user_type_attrs)),
    #             E.group(*(xml3), col="4", attrs=str(user_type_attrs)), name="groups_id", position="replace")
    #         xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))

    #     # serialize and update the view
    #     xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
    #     if xml_content != view.arch:  # avoid useless xml validation if no change
    #         new_context = dict(view._context)
    #         new_context.pop('install_filename', None)  # don't set arch_fs for this computed view
    #         new_context['lang'] = None
    #         view.with_context(new_context).write({'arch': xml_content})
