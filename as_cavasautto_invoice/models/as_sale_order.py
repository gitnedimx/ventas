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

class as_SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def desglosado_tax(self,lines):
        impuestos=[]
        if self.partner_id.x_studio__desglosa_ieps_ == True:
            return lines.tax_id
        else:
            for line_tax in lines.tax_id:
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
        taxes = line.tax_id
        for tax in taxes:
            if tax.name == 'IVA(16%) VENTAS':
                total_price = (1+(tax.amount/100))
        return float(total_price)

    @api.multi
    def monto_iva(self,line):
        total_price=0.00
        price_iva=0.00
        precio_sin_iva=0.00
        taxes = line.tax_id
        for tax in taxes:
            if tax.name == 'IVA(16%) VENTAS':
                total_price = (1+(tax.amount/100))
                precio_sin_iva=line.price_unit/total_price
                price_iva= precio_sin_iva * (tax.amount/100)
        return float(price_iva)
    
    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]

    