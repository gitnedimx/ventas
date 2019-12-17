# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from werkzeug.urls import url_encode

import logging
logger = logging.getLogger(__name__)

class as_accountinvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def desglosado_tax(self,lines):
        impuestos=[]
        if self.partner_id.x_studio__desglosa_ieps_ == True:
            return lines.invoice_line_tax_ids
        else:
            for line_tax in lines.invoice_line_tax_ids:
                if line_tax.id == 2:
                    impuestos.append(line_tax.id)
            taxes = self.env['account.tax'].search([('id', 'in', tuple(impuestos))])
            return taxes

    @api.multi
    def valor_usuario(self,amount_by_group):
        return self.partner_id.x_studio__desglosa_ieps_

    @api.multi
    def valor_sin_iva(self,amount_by_group):
        total_impuestos=0.00
        for impuesto in amount_by_group:
            if impuesto[0] != 'IVA 16% ':
                total_impuestos+= impuesto[1]
        return float(total_impuestos)

    @api.multi
    def price_sin_iva(self,line):
        total_price=0.00
        taxes = line.invoice_line_tax_ids
        for tax in taxes:
            if tax.name == 'IVA(16%) VENTAS':
                total_price = (1+(tax.amount/100))
        return float(total_price)

    @api.multi
    def monto_iva(self,line):
        total_price=0.00
        price_iva=0.00
        precio_sin_iva=0.00
        taxes = line.invoice_line_tax_ids
        for tax in taxes:
            if tax.name == 'IVA(16%) VENTAS':
                total_price = (1+(tax.amount/100))
                precio_sin_iva=line.price_unit/total_price
                price_iva= precio_sin_iva * (tax.amount/100)
        return float(price_iva)
