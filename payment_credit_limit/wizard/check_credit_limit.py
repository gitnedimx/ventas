# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApproveCreditLimit(models.TransientModel):
    _name = 'approval.credit.limit'
    _description = "Approval Credit limit"

    approved_amount = fields.Float(string='Approved Amount', copy=False)
    reason = fields.Text(string='Reason')

    @api.model
    def default_get(self, fields):
        rec = super(ApproveCreditLimit, self).default_get(fields)
        if self._context.get('active_id', False):
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            rec['approved_amount'] = order_id.amount_total
        return rec

    @api.multi
    def approved_credit_limit(self):
        if self._context.get('active_id', False):
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            if self.approved_amount > order_id.amount_total:
                raise UserError(_('Approval amount must be equal or less than %s ') % (order_id.amount_total))
            else:
                order_id.state = 'approved'
                order_id.approved_amount = self.approved_amount
                order_id.upgrade_approval = True
                order_id.write({'approval_history_ids': [(0, 0, {'approved_amount': self.approved_amount,
                                                                 'reason': self.reason, 'status': 'approved',
                                                                 'order_id': order_id.id})]})

    @api.multi
    def cancel_credit_limit(self):
        if self._context.get('active_id', False):
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            order_id.state = 'cancel'
            order_id.write({'approval_history_ids': [(0, 0, {'reason': self.reason, 'status': 'rejected',
                                                             'order_id': order_id.id})]})
