# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _default_branch_id(self):
        print ("sssssssssssssssssssssssssssssssssssssssssssss",self._context.get('branch_id'))
        if not self._context.get('branch_id'):
           branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        else:
           branch_id =  self._context.get('branch_id')
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)


    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue


            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            for line in iml:
                line['branch_id']=inv.branch_id.id
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)

            name = inv.name or ''
            if inv.payment_term_id:
                totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
                'branch_id':inv.branch_id.id
            }
            move = account_move.create(move_vals)
            # Pass invoice in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post(invoice = inv)
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.write(vals)
            for move_line in move.line_ids:
                move_line.branch_id  =  inv.branch_id.id    
        return True

    # @api.model
    # def invoice_line_move_line_get(self):
    #     res = []
    #     for line in self.invoice_line_ids:
    #         if not line.account_id:
    #             continue
    #         if line.quantity==0:
    #             continue
    #         tax_ids = []
    #         for tax in line.invoice_line_tax_ids:
    #             tax_ids.append((4, tax.id, None))
    #             for child in tax.children_tax_ids:
    #                 if child.type_tax_use != 'none':
    #                     tax_ids.append((4, child.id, None))
    #         analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
    #
    #         move_line_dict = {
    #             'invl_id': line.id,
    #             'type': 'src',
    #             'name': line.name,
    #             'price_unit': line.price_unit,
    #             'quantity': line.quantity,
    #             'price': line.price_subtotal,
    #             'account_id': line.account_id.id,
    #             'product_id': line.product_id.id,
    #             'uom_id': line.uom_id.id,
    #             'account_analytic_id': line.account_analytic_id.id,
    #             'analytic_tag_ids': analytic_tag_ids,
    #             'tax_ids': tax_ids,
    #             'invoice_id': self.id,
    #             'branch_id':self.branch_id.id
    #         }
    #         res.append(move_line_dict)
    #     return res

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount_total:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)

                analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in tax_line.analytic_tag_ids]
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount_total,
                    'quantity': 1,
                    'price': tax_line.amount_total,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'invoice_id': self.id,
                    'branch_id':self.branch_id.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else []
                })
                done_taxes.append(tax.id)
        return res

    @api.model
    def _anglo_saxon_purchase_move_lines(self, i_line, res):
        """Return the additional move lines for purchase invoices and refunds.

        i_line: An account.invoice.line object.
        res: The move line entries produced so far by the parent move_line_get.
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id
        if i_line.product_id and i_line.product_id.valuation == 'real_time' and i_line.product_id.type == 'product':
            # get the fiscal position
            fpos = i_line.invoice_id.fiscal_position_id
            # get the price difference account at the product
            acc = i_line.product_id.property_account_creditor_price_difference
            if not acc:
                # if not found on the product get the price difference account at the category
                acc = i_line.product_id.categ_id.property_account_creditor_price_difference_categ
            acc = fpos.map_account(acc).id
            # reference_account_id is the stock input account
            reference_account_id = i_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)['stock_input'].id
            diff_res = []
            # calculate and write down the possible price difference between invoice price and product price
            for line in res:
                if line.get('invl_id', 0) == i_line.id and reference_account_id == line['account_id']:
                    # valuation_price unit is always expressed in invoice currency, so that it can always be computed with the good rate
                    valuation_price_unit = company_currency._convert(
                        i_line.product_id.uom_id._compute_price(i_line.product_id.standard_price, i_line.uom_id),
                        inv.currency_id,
                        company=inv.company_id, date=fields.Date.today(), round=False,
                    )
                    line_quantity = line['quantity']

                    if i_line.product_id.cost_method != 'standard' and i_line.purchase_line_id:
                        po_currency = i_line.purchase_id.currency_id
                        po_company = i_line.purchase_id.company_id
                        #for average/fifo/lifo costing method, fetch real cost price from incomming moves
                        valuation_price_unit = po_currency._convert(
                            i_line.purchase_line_id.product_uom._compute_price(i_line.purchase_line_id.price_unit, i_line.uom_id),
                            inv.currency_id,
                            company=po_company, date=inv.date or inv.date_invoice, round=False,
                        )
                        stock_move_obj = self.env['stock.move']
                        valuation_stock_move = stock_move_obj.search([
                            ('purchase_line_id', '=', i_line.purchase_line_id.id),
                            ('state', '=', 'done'), ('product_qty', '!=', 0.0)
                        ])
                        if self.type == 'in_refund':
                            valuation_stock_move = valuation_stock_move.filtered(lambda m: m._is_out())
                        elif self.type == 'in_invoice':
                            valuation_stock_move = valuation_stock_move.filtered(lambda m: m._is_in())

                        if valuation_stock_move:
                            valuation_price_unit_total = 0
                            valuation_total_qty = 0
                            for val_stock_move in valuation_stock_move:
                                # In case val_stock_move is a return move, its valuation entries have been made with the
                                # currency rate corresponding to the original stock move
                                valuation_date = val_stock_move.origin_returned_move_id.date or val_stock_move.date_expected
                                valuation_price_unit_total += company_currency._convert(
                                    abs(val_stock_move.price_unit) * val_stock_move.product_qty,
                                    inv.currency_id,
                                    company=inv.company_id, date=valuation_date, round=False,
                                )
                                valuation_total_qty += val_stock_move.product_qty
                            valuation_price_unit = valuation_price_unit_total / valuation_total_qty
                            valuation_price_unit = i_line.product_id.uom_id._compute_price(valuation_price_unit, i_line.uom_id)
                            line_quantity = valuation_total_qty

                        elif i_line.product_id.cost_method == 'fifo':
                            # In this condition, we have a real price-valuated product which has not yet been received
                            valuation_price_unit = po_currency._convert(
                                i_line.purchase_line_id.price_unit, inv.currency_id,
                                company=po_company, date=inv.date or inv.date_invoice, round=False,
                            )

                    interim_account_price = valuation_price_unit * line_quantity
                    invoice_cur_prec = inv.currency_id.decimal_places

                    if float_compare(valuation_price_unit, i_line.price_unit, precision_digits=invoice_cur_prec) != 0 and float_compare(line['price_unit'], i_line.price_unit, precision_digits=invoice_cur_prec) == 0:

                        # price with discount and without tax included
                        price_unit = i_line.price_unit * (1 - (i_line.discount or 0.0) / 100.0)
                        tax_ids = []
                        if line['tax_ids']:
                            #line['tax_ids'] is like [(4, tax_id, None), (4, tax_id2, None)...]
                            taxes = self.env['account.tax'].browse([x[1] for x in line['tax_ids']])
                            price_unit = taxes.compute_all(price_unit, currency=inv.currency_id, quantity=1.0)['total_excluded']
                            for tax in taxes:
                                tax_ids.append((4, tax.id, None))
                                for child in tax.children_tax_ids:
                                    if child.type_tax_use != 'none':
                                        tax_ids.append((4, child.id, None))

                        price_before = line.get('price', 0.0)
                        price_unit_val_dif = price_unit - valuation_price_unit

                        price_val_dif = price_before - interim_account_price
                        if inv.currency_id.compare_amounts(i_line.price_unit, valuation_price_unit) != 0 and acc:
                            # If the unit prices have not changed and we have a
                            # valuation difference, it means this difference is due to exchange rates,
                            # so we don't create anything, the exchange rate entries will
                            # be processed automatically by the rest of the code.
                            diff_res.append({
                                'type': 'src',
                                'name': i_line.name[:64],
                                'price_unit': inv.currency_id.round(price_unit_val_dif),
                                'quantity': line_quantity,
                                'price': inv.currency_id.round(price_val_dif),
                                'account_id': acc,
                                'product_id': line['product_id'],
                                'uom_id': line['uom_id'],
                                'account_analytic_id': line['account_analytic_id'],
                                'tax_ids': tax_ids,
                            })
            return diff_res
        return []


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)
