# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    branch_id = fields.Many2one('res.branch')

    def _select(self):
        return super(PurchaseReport, self)._select() + ", s.branch_id as branch_id"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", s.branch_id"