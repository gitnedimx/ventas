# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_code_id = fields.Many2one('credit.code', 'Credit Code')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
