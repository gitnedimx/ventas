# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Bank(models.Model):
    _inherit = "res.bank"

    l10n_mx_edi_code = fields.Char(
        string="ABM Code",
        help="Three-digit number assigned by the ABM to identify banking"
        " institutions (ABM is an acronym for Asociación de Bancos de México)")


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_mx_edi_clabe = fields.Char(
        string='CLABE',
        help="Standardized banking cipher for Mexico. "
        "More info wikipedia.org/wiki/CLABE")
