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


    print_image = fields.Boolean(
        'Print Image', help="""If ticked, you can see the product image in
        report of sale order/quotation""")
    image_sizes = fields.Selection(
        [('image', 'Big sized Image'), ('image_medium', 'Medium Sized Image'),
         ('image_small', 'Small Sized Image')],
        'Image Sizes', default="image_small",
        help="Image size to be displayed in report")

    @api.multi
    def line_product_edit(self):
        posiciones_insigneas = []
        insignea=0
        bandera = False
        for line in self.order_line:
            if line.product_id.product_tmpl_id.x_studio_producto_insignia == True:
                line_venta={}
                if insignea == 0 and bandera== False:
                    bandera=True
                    insignea=0
                elif bandera==True:
                    insignea+=1
                line_venta= {
                        'image': line.product_id.image,
                        'price_total': line.price_total,
                        'display_type': line.display_type,
                        'display_type': line.display_type,
                        'display_type': line.display_type,
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.name,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'tax_id': line.tax_id,
                        'price_subtotal': line.price_subtotal,
                        'price_total': line.price_total,
                        'display_type ': line.display_type,
                        'name': line.name,
                        'display_type ': line.display_type ,
                        'name': line.name,
                        'material': line.product_id.product_tmpl_id.x_studio_material,
                        'medidas': line.product_id.product_tmpl_id.x_studio_medidas,
                        'aplicacion': '',
                    }
                posiciones_insigneas.append(line_venta)
            else:
                if line.product_id.product_tmpl_id.x_studio_sumar_descripcin_1 == True:
                    posiciones_insigneas[insignea]['name']= posiciones_insigneas[insignea]['name']+'/'+line.name
                    posiciones_insigneas[insignea]['price_subtotal']+=line.price_subtotal
                elif line.product_id.product_tmpl_id.x_studio_sumar_descripcin_1 == False and line.product_id.product_tmpl_id.x_studio_aplicacin_1 == False:
                    posiciones_insigneas[insignea]['price_subtotal']+=+line.price_subtotal
                if line.product_id.product_tmpl_id.x_studio_aplicacin_1 == True:
                    posiciones_insigneas[insignea]['aplicaciobol']= True
                    posiciones_insigneas[insignea]['aplicacion']= line.name
                    posiciones_insigneas[insignea]['price_subtotal']+=line.price_subtotal
                
        return posiciones_insigneas           

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    image_small = fields.Binary(
        'Product Image', related='product_id.image_small')
