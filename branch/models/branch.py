# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if self._context.get('branch_id'):
            recs = self.search([('id', 'in', self.env.user.branch_ids.ids)] + args, limit=limit)
            return recs.name_get()
        return super(ResBranch, self).name_search(name=name, args=args, operator=operator, limit=limit)