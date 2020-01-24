# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class account_bank_statement_line(models.Model):

    _inherit = 'account.bank.statement.line'

    @api.model
    def _get_bank_statement_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.uid).branch_id.id  or False
        return branch_id


    branch_id = fields.Many2one('res.branch', 'Branch', default=_get_bank_statement_default_branch , readonly = False)

