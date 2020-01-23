# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    approval_history_ids = fields.One2many('orderline.approval.history', 'order_id', string='Approval History')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('credit_hold', 'CC Hold'),
        ('approved', 'Approved'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    upgrade_approval = fields.Boolean(string='Approval based on Order Limit', copy=False)
    approved_amount = fields.Float(string='Approved Amount', copy=False)

    @api.multi
    def action_draft(self):
        res = super(SaleOrder,self).action_draft()
        self.approved_amount = False
        self.upgrade_approval = False
        return res

    @api.multi
    def action_confirm(self):
        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        for order in self:
            if order.state == 'draft':
                order.confirmation_date = fields.Datetime.now()
                order.action_create_do()
                if self.env.context.get('send_email'):
                    order.force_quotation_send()
        if self.env['ir.config_parameter'].get_param('sale.auto_done_setting'):
            self.action_done()

    @api.multi
    def action_create_do(self):
        for order in self:
            if order.order_line:
                if order.state in ['draft', 'credit_hold', 'approved']:
                    if order.partner_id.credit_limit > 0:
                        check_false = self.env['credit.code'].check_approval_status(order.id)
                        if not check_false and order.amount_total > 0.0:
                            order.state = 'credit_hold'
                        else:
                            order.state = 'sale'
                    else:
                        order.state = 'sale'

    @api.multi
    def delivery_order(self):
        for order in self:
            if order.approved_amount < order.amount_total and order.upgrade_approval:
                raise UserError(_('First reduce order qauntity base on your Approved amount!'))
            else:
                order.order_line._action_launch_stock_rule()
                order.state = 'sale'

    @api.multi
    def credit_approve(self):
        if not self.env.user.has_group('sales_team.group_sale_manager') and (self.env.user.id == self.user_id.id):
            raise UserError(_('You can not approve own record!'))
        else:
            view_id = self.env.ref('payment_credit_limit.view_approval_credit_limit', False)

            return {'type': 'ir.actions.act_window',
                    'name': _('Approval Credit Limit'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'approval.credit.limit',
                    'target': 'new',
                    'views': [(view_id.id, 'form')],
                    'view_id': view_id.id,
                    }

    @api.multi
    def cancel_order_on_cc(self):
        if self.env.user.id == self.user_id.id:
            raise UserError(_('You can not reject own record!'))
        else:
            view_id = self.env.ref('payment_credit_limit.view_cancel_credit_limit', False)
            return {'type': 'ir.actions.act_window',
                    'name': _('Cancel Approval'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'approval.credit.limit',
                    'target': 'new',
                    'views': [(view_id.id, 'form')],
                    'view_id': view_id.id,
                    }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_launch_stock_rule(self):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if not line.product_id.type in ('consu','product'):
                continue
            qty = 0.0
            for move in line.move_ids.filtered(lambda r: r.state != 'cancel'):
                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        orders = list(set(x.order_id for x in self))
        for order in orders:
            reassign = order.picking_ids.filtered(lambda x: x.state=='confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
            if reassign:
                reassign.do_unreserve()
                reassign.action_assign()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
