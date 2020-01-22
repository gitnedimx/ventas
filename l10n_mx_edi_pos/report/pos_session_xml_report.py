# coding: utf-8
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError as err:
    _logger.debug(err)


class SessionXmlReport(models.AbstractModel):
    _name = "report.l10n_mx_edi_pos.report_xml_session"
    _description = "XML report for POS session"

    @api.multi
    def _get_report_values(self, docids, data=None):
        sessions = self.env['pos.session'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'pos.session',
            'docs': sessions,
            'cfdi': data.get('cfdi', ''),
            'amount_to_text': self._amount_to_text,
        }

    def _amount_to_text(self, amount):
        total = str(float(amount)).split('.')[0]
        decimals = str(float(amount)).split('.')[1]
        currency_type = 'M.N.'
        currency = 'PESOS'
        total = num2words(float(total), lang='es').upper()
        return '%s %s %s/100 %s' % (
            total, currency, decimals or 0.0, currency_type)
