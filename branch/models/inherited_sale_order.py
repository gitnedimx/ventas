# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    @api.model
    def default_get(self,fields):
        res = super(SaleOrder, self).default_get(fields)
        user_branch = self.env['res.users'].browse(self.env.uid).branch_id
        if user_branch:
            branched_warehouse = self.env['stock.warehouse'].search([('branch_id','=',user_branch.id)])
            if branched_warehouse:
                res['warehouse_id'] = branched_warehouse.ids[0]
            else:
                res['warehouse_id'] = False

        return res


    branch_id = fields.Many2one('res.branch', default=_default_branch_id)

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['branch_id'] = self.branch_id.id
        return res
