# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import operator as o

OPERATOR_MAP = {
    '=': o.eq,
    '==': o.eq,
    '>=': o.ge,
    '<=': o.le,
    '<': o.lt,
    '>': o.gt
}

OPERATOR_CONDITION = {
    '==': '=',
    '<=': '>=',
    '<': '>',
    '>=': '<=',
    '>': '<'
}


class CreditCode(models.Model):
    _inherit = "credit.code"
    _order = "code"

    code = fields.Integer('Code', required=True, help="Code of credit code rule.")
    name = fields.Char('Name', required=True, help="Name of credit code rule.")
    description = fields.Text('Description', help="Description of credit code rule.")
    credit_check = fields.Selection([('credit_hold', 'Credit Hold'),
                                    ('check_limit', 'Check Limit'),
                                    ('unlimited_account', 'Unlimited Account'),
                                    ('base_on_rule', 'Based on Rules')],
                                string='Check Credit', default='check_limit', required=True, help="Credit check type.")
    credit_limit_enforced = fields.Boolean('Credit Limit Enforced?', help="Compulsory check credit limit.")
    line_ids = fields.One2many('credit.code.line', 'credit_code_id','Credit Code Rules',
                               help="Check credit code conditions.")
    active = fields.Boolean(default=True)

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for credit_code in self:
            name = '[' + str(credit_code.code) + '] ' + credit_code.name
            result.append((credit_code.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        records = self.search([])
        if name:
            ids = self.search(['|', ('name', 'ilike', name), ('code', 'ilike', name)]+ args, limit=limit)
            if records and ids:
                records = self.browse(list(set(records.ids).intersection(ids.ids)))
            elif ids:
                records = ids
        return records.name_get()

    @api.multi
    @api.constrains('code')
    def check_code_unique(self):
        if self.code:
            find_code = self.search([('code', '=', self.code), ('id', '!=', self.id)])
            if find_code:
                raise UserError(_('The code must be unique per credit code!'))

    @api.multi
    def calculate_onorder_amount(self, partner, operator_condition, days, sale_order, partner_currency_id):
        past_total_amount = 0.0
        past_due_amt = 0.0
        cr = self.env.cr
        myTime = datetime.strptime(str(sale_order.date_order), "%Y-%m-%d %H:%M:%S").date()
        check_date = myTime - timedelta(days=days)
        operator_condition = OPERATOR_CONDITION[operator_condition]
        user_company = self.env.user.company_id.id

        # calculate partner credit amount.
        dates_query = '(l.date_maturity '
        dates_query += operator_condition
        dates_query += ' %s)'
        query = '''SELECT l.id
                FROM account_move_line AS l,
                account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN ('draft', 'posted'))
                    AND (account_account.internal_type IN ('receivable'))
                    AND (l.partner_id = %s)
                    AND l.company_id = %s
                    AND ''' + dates_query + '''
                    '''
        cr.execute(query, [partner, user_company, check_date])
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            open_amount = line.balance
            if line.currency_id and line.currency_id.id != partner_currency_id.id:
                open_amount = line.currency_id.compute(open_amount, partner_currency_id)
            past_due_amt += open_amount
        # calculate draft account invoices past due amount
        account_invoice_search = self.env['account.invoice'].search([('partner_id', '=', partner), ('state', '=', 'draft')])
        if account_invoice_search:
            for account_invoice in account_invoice_search:
                if account_invoice.payment_term_id:
                    totlines = account_invoice.payment_term_id.with_context(currency_id=account_invoice.currency_id.id).compute(account_invoice.amount_total, account_invoice.date_invoice)[0]
                    for total_line in enumerate(totlines):
                        open_amount = total_line[1][1]
                        if not account_invoice.currency_id == partner_currency_id:
                            open_amount = account_invoice.currency_id.compute(total_line[1][1], partner_currency_id)
                        date = datetime.strptime(total_line[1][0], "%Y-%m-%d").date()
                        if check_date >= date:
                            if account_invoice.type == 'out_invoice':
                                past_due_amt += open_amount
                            elif account_invoice.type == 'out_refund':
                                past_due_amt -= open_amount
                else:
                    open_amount = account_invoice.amount_total
                    if not account_invoice.currency_id == partner_currency_id:
                        open_amount = account_invoice.currency_id.compute(account_invoice.amount_total, partner_currency_id)
                    if account_invoice.type == 'out_invoice':
                        past_due_amt += open_amount
                    elif account_invoice.type == 'out_refund':
                        if past_due_amt >= open_amount:
                            past_due_amt -= open_amount
        past_total_amount = past_due_amt
        return past_total_amount

    @api.multi
    def calculate_based_on(self, credit_limit, past_due_amt, rule_of, based_amt, based_opt, value):
        if rule_of == 'past_due':
            if based_amt == 'percentage':
                amt = ((past_due_amt * value) / 100)
                check = OPERATOR_MAP[based_opt](amt, past_due_amt)
                return True if check else False
            elif based_amt == 'amount':
                check = OPERATOR_MAP[based_opt](past_due_amt, value)
                return True if check else False
        elif rule_of == 'credit_limit':
            if based_amt == 'percentage':
                amt = ((credit_limit * value) / 100)
                check = OPERATOR_MAP[based_opt](amt, past_due_amt)
                return True if check else False
            elif based_amt == 'amount':
                check = OPERATOR_MAP[based_opt](past_due_amt, value)
                return True if check else False

    @api.multi
    def calculate_due_amount(self, partner, operator_condition, days, sale_order, partner_currency_id):
        past_total_amount = 0.0
        past_due_amt = 0.0
        cr = self.env.cr
        myTime = datetime.strptime(str(sale_order.date_order), "%Y-%m-%d %H:%M:%S").date()
        check_date = myTime - timedelta(days=days)
        operator_condition = OPERATOR_CONDITION[operator_condition]
        user_company = self.env.user.company_id.id

        # calculate partner credit amount.
        dates_query = '(l.date_maturity '
        dates_query += operator_condition
        dates_query += ' %s)'
        query = '''SELECT l.id
                FROM account_move_line AS l,
                account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN ('draft', 'posted'))
                    AND (account_account.internal_type IN ('receivable'))
                    AND (l.partner_id = %s)
                    AND l.company_id = %s
                    AND ''' + dates_query + '''
                    '''
        cr.execute(query, [partner, user_company, check_date])
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            open_amount = line.balance
            if line.currency_id and line.currency_id.id != partner_currency_id.id:
                open_amount = line.currency_id.compute(open_amount, partner_currency_id)
            past_due_amt += open_amount
        past_total_amount = past_due_amt
        return past_total_amount

    @api.multi
    def check_approval_status(self, sale_order_id):
        past_due_amt = 0.0
        temp = False
        account_invoice_obj = self.env['account.invoice']
        sale_order = self.env['sale.order'].browse(sale_order_id)
        partner = self.env['res.partner']._find_accounting_partner(sale_order.partner_id)
        delivery_date = datetime.now().date()
        if not partner.credit_code_id:
            so_on_order_amount = 0
            for orderline in self.env['sale.order'].search([('partner_id', '=', partner.id), ('state', '=', 'sale')]):
                so_on_order_amount += orderline.amount_total
            total_amount = so_on_order_amount + sale_order.amount_total
            past_total_amount = past_due_amt + total_amount
            if partner.credit_limit >= past_total_amount:
                return True
            else:
                return False
        else:
            credit_check = partner.credit_code_id.credit_check
            if credit_check == 'credit_hold':
                return False
            elif credit_check == 'check_limit':
                past_due_amt = partner.credit
                account_invoice_search = account_invoice_obj.search([('partner_id', '=', partner.id), ('state', '=', 'draft')])
                for account_invoice in account_invoice_search:
                    if account_invoice.payment_term_id:
                        totlines = account_invoice.payment_term_id.with_context(currency_id=account_invoice.currency_id.id).compute(account_invoice.amount_total, account_invoice.date_invoice)[0]
                        for total_line in enumerate(totlines):
                            date = datetime.strptime(total_line[1][0], "%Y-%m-%d").date()
                            if delivery_date >= date:
                                past_due_amt += total_line[1][1]
                                if account_invoice.type == 'out_invoice':
                                    past_due_amt += total_line[1][1]
                                elif account_invoice.type == 'out_refund':
                                    past_due_amt -= total_line[1][1]
                    else:
                        if account_invoice.date_due and delivery_date >= account_invoice.date_due:
                            if account_invoice.type == 'out_invoice':
                                past_due_amt += account_invoice.amount_total
                            elif account_invoice.type == 'out_refund':
                                past_due_amt -= account_invoice.amount_total
                past_total_amount = past_due_amt + sale_order.amount_total
                if not sale_order.pricelist_id.currency_id == partner.currency_id:
                    past_total_amount = sale_order.pricelist_id.currency_id.compute(past_total_amount, partner.currency_id)
                return True if partner.credit_limit >= past_total_amount else False
            elif credit_check == 'unlimited_account':
                return True
            elif credit_check == 'base_on_rule':
                for rule_line in partner.credit_code_id.line_ids:
                    days = rule_line.days
                    if not rule_line.of:
                        past_due_amt = self.calculate_due_amount(partner.id, rule_line.operator_condition, days, sale_order, partner.currency_id)
                        if past_due_amt > 0.0:
                            temp = True
                            # return False
                        else:
                            temp = False
                    elif rule_line.of:
                        past_due_amt = self.calculate_due_amount(partner.id, rule_line.operator_condition, days, sale_order, partner.currency_id)
                        if past_due_amt > 0.0:
                            based_on = self.calculate_based_on(partner.credit_limit, past_due_amt, rule_line.of, rule_line.based_on_amount, rule_line.operator_based_on, rule_line.value)
                            if based_on:
                                temp = True
                            else:
                                temp = False
                if temp:
                    return False
                else:
                    if partner.credit_code_id.credit_limit_enforced:
                        past_due_amt = self.calculate_onorder_amount(partner.id, '>=', 0, sale_order, partner.currency_id)
                        past_total_amount = past_due_amt + sale_order.amount_total
                        return True if partner.credit_limit >= past_total_amount else False
                    else:
                        return True


class CreditCodeLine(models.Model):
    _name = "credit.code.line"
    _order = "sequence"

    sequence = fields.Integer('Sequence', required=True, default=5)
    credit_code_id = fields.Many2one('credit.code', 'Credit Code', ondelete='cascade')
    name = fields.Char(compute='_get_name')
    check_past = fields.Selection([('past_due', 'Past Due')], 'Check Past',
                                  required=True, default='past_due', help="Check type of amount.")
    operator_condition = fields.Selection([('==', '='), ('<=', '<='), ('<', '<'), ('>=', '>='), ('>', '>')],
                                          'Operator Condition', required=True,
                                          default='<=', help="Operator condition")
    days = fields.Integer('Days', required=True, help="Number of days used for calculate past due amount.")
    of = fields.Selection([('past_due', 'Past Due'), ('credit_limit', 'Credit Limit')], 'Of',
                          help="Check limit based on past due amount or credit limit.")
    based_on_amount = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')],
                                       'Based on Amount', help="Based on amount like percentage or fixed amount.")
    operator_based_on = fields.Selection([('==', '='), ('<=', '<='), ('<', '<'), ('>=', '>='), ('>', '>')],
                                         'Operator Based on', help="Operator condition")
    value = fields.Float('Value', help="Value fill based on amount selection like percentage or fixed amount.")

    @api.depends('check_past', 'operator_condition', 'operator_based_on',
                 'value', 'of', 'days', 'based_on_amount')
    def _get_name(self):
        for rule in self:
            name = ' if %s %s %s days then approval needed on any amount.' % (rule.check_past, rule.operator_condition, rule.days)
            rule.name = name

    @api.onchange('of')
    def onchange_of_selection(self):
        if not self.of:
            self.based_on_amount = False
            self.operator_based_on = False
            self.value = False


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        date_invoice = self.date_invoice
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        if not self.payment_term_id:
            # When no payment term defined
            self.date_due = self.date_invoice
        else:
            pterm = self.payment_term_id
            pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1,
                                                                                                date_ref=date_invoice)[0]
            self.date_due = max(line[0] for line in pterm_list)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
