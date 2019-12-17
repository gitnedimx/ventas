# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method', string='Payment Way',
        help='Indicates the payment way the orders was/will be paid, where '
        'the options could be: Cash, Nominal Check, Credit Card, etc. Leave '
        'empty if unknown and the XML will show "Unidentified".')
