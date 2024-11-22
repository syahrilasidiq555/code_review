from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import get_timedelta

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from odoo.tools import format_date

class sale_order_subscription(models.Model):
    _inherit = 'sale.order'

    def _update_next_invoice_date(self):
        for order in self:
            if not order.is_subscription:
                continue
            last_invoice_date = order.next_invoice_date or datetime(day=order.end_date.day, month=order.start_date.month, year=order.start_date.year) #order.start_date
            if last_invoice_date:
                order.next_invoice_date = last_invoice_date + order.plan_id.billing_period

    @api.depends('is_subscription', 'state', 'start_date', 'subscription_state')
    def _compute_next_invoice_date(self):
        for so in self:
            if not so.is_subscription and so.subscription_state != '7_upsell':
                so.next_invoice_date = False
            elif not so.next_invoice_date and so.state == 'sale':
                # Define a default next invoice date.
                # It is increased by _update_next_invoice_date or when posting a invoice when when necessary
                so.next_invoice_date = so.start_date or fields.Date.today()

# so._compute_start_date()
# next_periode = self.start_date + relativedelta(months=1)
# so.next_invoice_date = datetime(so.start_date.year, next_periode.month, so.end_date.day)

# class SaleSubscriptionPlan(models.Model):
#     _inherit = 'sale.subscription.plan'

#     @property
#     def billing_period(self):
#         if not self.billing_period_unit or not self.billing_period_value:
#             return False
#         else:

#         return get_timedelta(self.billing_period_value, self.billing_period_unit)

class sale_order_line_subscription(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)
        if self.display_type:
            return res
        elif self.order_id.plan_id and (self.recurring_invoice or self.order_id.subscription_state == '7_upsell'):
            lang_code = self.order_id.partner_id.lang
            if self.order_id.subscription_state == '7_upsell':
                # We start at the beginning of the upsell as it's a part of recurrence
                new_period_start = max(self.order_id.start_date or fields.Date.today(), self.order_id.first_contract_date)
            else:
                # We need to invoice the next period: last_invoice_date will be today once this invoice is created. We use get_timedelta to avoid gaps
                # We always use next_invoice_date as the recurrence are synchronized with the invoicing periods.
                # Next invoice date is required and is equal to start_date at the creation of a subscription
                new_period_start = self.order_id.next_invoice_date
            parent_order_id = self.order_id.id
            if self.order_id.subscription_state == '7_upsell':
                # remove 1 day as normal people thinks in terms of inclusive ranges.
                next_invoice_date = self.order_id.next_invoice_date - relativedelta(days=1)
                parent_order_id = self.order_id.subscription_id.id
            else:
                default_next_invoice_date = new_period_start + self.order_id.plan_id.billing_period
                default_next_invoice_date = datetime(default_next_invoice_date.year, default_next_invoice_date.month, self.order_id.end_date.day) # set day same as date end
                # remove 1 day as normal people thinks in terms of inclusive ranges.
                next_invoice_date = default_next_invoice_date - relativedelta(days=1)

            description = self.name
            if self.recurring_invoice:
                duration = self.order_id.plan_id.billing_period_display
                format_start = format_date(self.env, new_period_start, lang_code=lang_code)
                format_next = format_date(self.env, next_invoice_date, lang_code=lang_code)
                start_to_next = _("\n%s to %s", format_start, format_next)
                description = f"{description} - {duration}{start_to_next}"

            qty_to_invoice = self._get_subscription_qty_to_invoice(last_invoice_date=new_period_start,
                                                                   next_invoice_date=next_invoice_date)
            deferred_end_date = next_invoice_date
            res['quantity'] = qty_to_invoice.get(self.id, 0.0)

            # set prorate unit price
            new_price = res['price_unit']
            diff = relativedelta(deferred_end_date, new_period_start)
            if diff.months < 1:
                new_price = (new_price / 30) * diff.days

            res.update({
                'name': description,
                'deferred_start_date': new_period_start,
                'deferred_end_date': deferred_end_date,
                'subscription_id': parent_order_id,
                'price_unit': new_price,
            })
        elif self.order_id.is_subscription:
            # This is needed in case we only need to invoice this line
            res.update({
                'subscription_id': self.order_id.id,
            })
        return res
