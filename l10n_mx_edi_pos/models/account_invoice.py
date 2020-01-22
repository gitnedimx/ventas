# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        """Set payment method and usage"""
        res = super()._onchange_partner_id()
        if self.env.context.get('force_payment_method'):
            self.l10n_mx_edi_payment_method_id = self.env.context.get(
                'force_payment_method')
        return res
