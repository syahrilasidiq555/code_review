from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Product(models.Model):
    _inherit = 'product.template'

    minimum_stock = fields.Integer(string='Minimum Stock', default=0)

    # lokasi product
    product_location_id = fields.Many2one('product.location', string="Lokasi Product", store=True)

    # def send_low_stock_via_email(self, cr, uid, context=None):
    def send_low_stock_via_email(self):
        body_message_channel = """
            <h3>Low Stock Notification</h3>
            <br>
            <table class="table table-striped table-bordered nowrap" style="font-size:12px;" width="100%">
                <col style="width:8%"/>
                <col style="width:15%"/>
                <col style="width:20%"/>
                <col style="width:15%"/>
                <col style="width:17%"/>
                <col style="width:8%"/>
                <thead class="thead-light">
                    <tr>
                        <th scope="col" style="text-align:center;">#</th>
                        <th scope="col" style="text-align:center;">Product</th>
                        <th scope="col" style="text-align:center;">Qty On Hand</th>
                        <th scope="col" style="text-align:center;">Qty Incoming</th>
                        <th scope="col" style="text-align:center;">Minimum Stock</th>
                        <th scope="col" style="text-align:center;"></th>
                    </tr>
                </thead>
                <tbody>
        """

        count = 0
        product_obj  = self.env['product.product'].search([('active', '=', True)])
        for line in product_obj:
            ir_action_id = self.env.ref('stock.product_template_action_product')
            ir_ui_menu_id = self.env.ref('stock.menu_product_variant_config_stock')
            base = self.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')],limit=1)
            url = '{baseurl}/web#id={record_id}&menu_id={menu_id}&action={action_id}&model={model_name}&view_type=form&cids=1'.format(
                baseurl = base[0].value,
                record_id = line.product_tmpl_id.id,
                action_id = ir_action_id.id,
                model_name = 'product.template', #line._name,
                menu_id = ir_ui_menu_id.id
            )

            count += 1
            qty_available = line.qty_available
            qty_incoming  = line.incoming_qty
            qty_low_stock_notify = line.minimum_stock
            if qty_available <= qty_low_stock_notify and qty_low_stock_notify >= 0: ## set low_stock_notify = -1 to never be notified
                body_message_channel += """
                    <tr style="font-size:14px;">
                        <td>%s</td>
                        <td>%s</td>
                        <td style="text-align:center;">%s</td>
                        <td style="text-align:center;">%s</td>
                        <td style="text-align:center;">%s</td>
                        <td style="text-align:center;">
                            <a href="%s" target="_blank">Go To Product</a>
                        </td>
                    </tr>
                """ %(str(count), str(line.name), str(qty_available), str(qty_incoming), str(qty_low_stock_notify), url)

        body_message_channel += """
            </tbody>
            </table>
        """

        notification_ids = [((0, 0, {
            'res_partner_id': self.env.user.partner_id.id,
            'notification_type': 'inbox'}))]
        chnl_id = self.env.ref('custom_inventory.channel_low_stock').id 
        chnl = self.env['mail.channel'].search([('id', '=', chnl_id)])
        if chnl:
            chnl.message_post(author_id=self.env.user.id,
                        body=(body_message_channel),
                        message_type='notification',
                        subtype_xmlid="mail.mt_comment",
                        notification_ids=notification_ids,
                        partner_ids=[self.env.user.partner_id.id],
                        notify_by_email=False,
                        )
        
class ProductLocation(models.Model):
    _name = 'product.location'
    _description = 'Lokasi Product'

    name = fields.Char(string='Name', tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)

# class ProductCategory(models.Model):
#     _inherit = 'product.category'

#     property_stock_account_delivery_categ_id = fields.Many2one(
#         'account.account', 'Stock Delivery Account', company_dependent=True,
#         domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
#         help="""When doing automated inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account,
#                 unless there is a specific valuation account set on the destination location. This is the default value for all products in this category.
#                 It can also directly be set on each product.""")
    
#     @api.constrains('property_stock_valuation_account_id', 'property_stock_account_output_categ_id', 
#                     'property_stock_account_input_categ_id', 'property_stock_account_delivery_categ_id')
#     def _check_valuation_accouts(self):
#         # Prevent to set the valuation account as the input or output account.
#         for category in self:
#             valuation_account = category.property_stock_valuation_account_id
#             input_and_output_accounts = category.property_stock_account_input_categ_id | category.property_stock_account_output_categ_id | category.property_stock_account_delivery_categ_id
#             if valuation_account and valuation_account in input_and_output_accounts:
#                 raise ValidationError(_('The Stock Input and/or Output accounts cannot be the same as the Stock Valuation account.'))