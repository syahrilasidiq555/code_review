from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        context={"res_partner_search_mode": "supplier","default_is_vendor": True},
        domain=[('is_vendor', '=', True)]
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res["supplier_id"] = False
        return res

    def make_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["purchase.request.line"]
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(_("Enter a positive quantity."))
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.currency_id,
                    line.origin,
                    line.date_start,
                )
                purchase = purchase_obj.create(po_data)
                purchase._onchange_amount_total_approval_type()
                purchase._onchange_loa_type()

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            # If Unit of Measure is not set, update from wizard.
            if not line.product_uom_id:
                line.product_uom_id = item.product_uom_id
            # Allocation UoM has to be the same as PR line UoM
            alloc_uom = line.product_uom_id
            wizard_uom = item.product_uom_id
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
                po_line.move_dest_ids |= line.move_dest_ids
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            else:
                po_line_data = self._prepare_purchase_order_line(purchase, item)
                if item.keep_description:
                    po_line_data["name"] = item.name
                po_line = po_line_obj.create(po_line_data)
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            # TODO: Check propagate_uom compatibility:
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line, new_pr_line=new_pr_line
            )
            po_line.product_qty = new_qty
            po_line._onchange_quantity()
            # The onchange quantity is altering the scheduled date of the PO
            # lines. We do not want that:
            date_required = fields.Datetime.to_datetime(item.line_id.date_required)
            context_date = fields.Datetime.context_timestamp(self, date_required)
            po_line.date_planned = date_required - context_date.utcoffset()
            for i in purchase.order_line:
                idx = len(i.purchase_request_lines.purchase_lines)-1
                if i.purchase_request_lines.purchase_lines[idx]:
                    purchase.sudo().write({
                        'yes_no':i.purchase_request_lines.purchase_lines[idx].order_id.yes_no,
                        'alasan':i.purchase_request_lines.purchase_lines[idx].order_id.alasan,
                        })
                    break
            res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }

    @api.model
    def _prepare_purchase_order(
        self, picking_type, group_id, company, currency, origin, start_date,
    ):
        if not self.supplier_id:
            raise UserError(_("Enter a supplier."))
        supplier = self.supplier_id
        data = {
            "origin": origin,
            "partner_id": self.supplier_id.id,
            "fiscal_position_id": supplier.property_account_position_id
            and supplier.property_account_position_id.id
            or False,
            "picking_type_id": picking_type.id,
            "company_id": company.id,
            "currency_id": currency.id,
            "group_id": group_id.id,
            "date_order": start_date,
        }
        return data
