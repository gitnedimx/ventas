# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models, fields, api, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    l10n_mx_edi_ticket_number = fields.Char(
        string="Ticket Number", index=True, copy=False,
        help='Unique number used to identify and download this ticket in '
        'our site',
        oldname="ticket_number")

    _sql_constraints = [
        ('ticket_number_unique',
         'unique(l10n_mx_edi_ticket_number,company_id)',
         'The ticket number must be unique')
    ]

    @api.model
    def _order_fields(self, ui_order):
        """Adding the new ticket_number"""
        res = super(PosOrder, self)._order_fields(ui_order)
        res['l10n_mx_edi_ticket_number'] = ui_order['ticket_number']
        return res

    @api.model
    def get_customer_cfdi(self, ticket_number):
        """Three things can happen in this method:

        a) The given ticket number already has an invoice. If this happens,
        a dictionary with an `invoice` key will be returned.

        b) The ticket number has a partner with valid data, but the ticket has
        no invoice. If this happens, the process of generating the invoice of
        the pos ticket will be triggered, and a dictionary with a `invoice` key
        will be returned.

        c) The ticket has no partner and has no invoice. This will return
        a dictionary with a `partner` key set to `No partner`, indicating that
        a partner was not found for that ticket. This will result in triggering
        the process of requiring input data from the user.

        :param ticket_number: the ticket number to invoice.
        :type ticket_number: str

        :return: a dictionary containing the result of the process
        :rtype: Dictionary
        """
        order = self.search([
            ('l10n_mx_edi_ticket_number', '=', ticket_number),
            ], limit=1)
        partner = order.partner_id
        # We are gonna use the partner in the order if this has a vat and this
        # is not generic
        valid_partner = (
            partner
            if (partner.vat and partner.vat != 'XEXX010101000') else False)
        invoice = order.invoice_id
        if invoice.l10n_mx_edi_pac_status != 'signed':
            invoice = valid_partner and self.invoice_sale(ticket_number)
        values = {
            'ticket_number': ticket_number,
            'partner': not partner.vat and _('No partner'),
            'invoice': invoice,
            'email': partner.email,
        }
        return values

    @api.model
    def update_partner(self, ticket_number, vat=None, email=None):
        """Used to parse the data received from the form where the email and
        the VAT are captured.

        Several things can happen here:

        a) If a partner is found with the data provided by the customer in
        the website form with matching VAT and Email, it will link the pos
        order to the user and will invoice it.

        b) If a partner is found with the data provided by the customer in
        the website form with a matching VAT but not matching Email, it will
        create a new contact to the matching partner, link it to the order and
        invoice the order.

        c) If a partner is found with the email provided but the customer has
        no VAT, it will be required to capture the VAT on the input form.

        d) If no customer found with any of the data provided it will create
        a new partner, link it to the order and invoice it.

        :param ticket_number: The ticket to relate to the partner.
        :type ticket_number: str

        :param vat: The VAT captured in the website form on which the
        customer can be created or searched by.
        :type vat: str

        :param email: The email captured in the website form on which the
        customer can be created or seached by.
        :type email: str

        :return: A dictionary with error or the invoice created.
        :rtype: dict
        """
        partner_obj = self.env['res.partner']
        values = {'ticket_number': ticket_number}
        order = self.search([
            ('l10n_mx_edi_ticket_number', '=', ticket_number),
            ], limit=1)
        if not order:
            values['vat'] = _('Required')
            values['error'] = _(
                'The order was not found. Please check the code')
            return values
        domain = [('vat', '=', vat)] if vat else [('email', '=ilike', email)]
        partner = partner_obj.search(domain, limit=1)
        if (partner and order.partner_id.vat
                and order.partner_id.vat != partner.vat):
            values['error'] = _(
                'The VAT in the order is different to the vat filled out by '
                'you. Please check it and try again')
            return values

        elif partner and order.partner_id and (order.partner_id != partner):
            order.partner_id.write({'parent_id': partner.id,
                                    'email': email})
            values['invoice'] = (
                order.invoice_id
                if order.invoice_id.l10n_mx_edi_pac_status == 'signed' else
                self.invoice_sale(ticket_number))
            return values
        elif partner:
            if ((partner.email or '').lower() != (email or '').lower() and not
                    partner_obj.search_count(
                        [('email', '=ilike', email),
                         ('parent_id', '=', partner.id)])):
                contact = partner_obj.create({
                    'name': email,
                    'email': email,
                    'parent_id': partner.id,
                })
            if order.partner_id:
                order.partner_id.write({
                    'vat': partner.vat or vat,
                    'email': partner.email or email,
                })
            else:
                order.write({
                    'partner_id': contact.id or partner.id,
                })
            values['invoice'] = (
                order.invoice_id
                if order.invoice_id.l10n_mx_edi_pac_status == 'signed' else
                self.invoice_sale(ticket_number))
            return values
        elif vat:
            new_data = {
                'country_id': self.env.ref('base.mx').id,
                'name': order.partner_id.name or email or vat,
                'vat': vat,
                'email': (order.partner_id.email and
                          email and
                          '%s;%s' % (order.partner_id.email, email) or
                          email or ''),
            }
            new_partner = (order.partner_id or
                           partner_obj.create(new_data))
            (order.partner_id or order).write(
                order.partner_id and new_data or
                {'partner_id': new_partner.id})
            values['invoice'] = (
                order.invoice_id
                if order.invoice_id.l10n_mx_edi_pac_status == 'signed' else
                self.invoice_sale(ticket_number))
            return values
        values['vat'] = _('Required')
        values['error'] = _('You are not registered, VAT is required')
        return values

    @api.multi
    def _get_invoice_from_close_session(self):
        """Get the invoice after the session was closed. When this happens it
        is needed to generate a new session to generate a new order with an
        invoice valid to generate the xml signed

        :return: The invoice generated if the order is in a valid range of time
        :rtype: account.invoice()
        """
        config = self.env.ref(
            'l10n_mx_edi_website.pos_config_download_electronic_invoice')
        config.active = True
        session_obj = self.env['pos.session']
        session = session_obj.search(
            [('user_id', '=', self._uid),
             ('state', 'not in', ('closed', 'closing_control')),
             ('name', 'not like', 'RESCUE FOR')],
            limit=1) or session_obj.create(
                {'user_id': self._uid,
                 'config_id': config.id})
        partner_id = self.partner_id.id
        ticket_number = self.l10n_mx_edi_ticket_number
        self.write({'partner_id': False,
                    'l10n_mx_edi_ticket_number': None})
        session.action_pos_session_open()
        returns = self.refund()
        returns = self.browse(returns.get('res_id'))
        # To be sure that the record is in my session
        returns.write(
            {'session_id': session.id,
             'note': _('Created to generate a new order '
                       'and generate the invoice')})
        payment_obj = self.env['pos.make.payment']
        journal = self.statement_ids and self.statement_ids[0].journal_id
        payment = payment_obj.with_context({'active_id': returns.id}).create({
            'journal_id': journal.id,
            'amount': returns.amount_total,
        })
        # Generate a new order
        payment.check()
        new_order = self.copy({
            'session_id': session.id,
            'partner_id': partner_id,
            'l10n_mx_edi_ticket_number': ticket_number,
        })
        payment_ctx = {'active_id': new_order.id}
        payment = payment_obj.with_context(payment_ctx).create({
            'journal_id': journal.id,
            'amount': new_order.amount_total,
        })
        payment.check()
        new_order.action_pos_order_invoice()
        session.action_pos_session_close()
        session.action_pos_session_closing_control()
        config.active = False
        return new_order.invoice_id

    @api.model
    def _get_invoice_from_open_session(self):
        """Generate the needed invoice from an order with an open session in a
        valid range of date"""
        self.action_pos_order_invoice()
        return self.invoice_id

    @api.model
    def invoice_sale(self, ticket_number):
        """Given a ticket_number it will trigger all the invoicing process for
        the given partner on the `pos.order`.

        :param ticket_number: The number of ticket to invoice.
        :type ticket_number: Integer

        :return: The new invoice just created.
        :rtype: account.invoice()
        """
        order = self.search([
            ('l10n_mx_edi_ticket_number', '=', ticket_number),
            ], limit=1)
        invoice = order.invoice_id
        session = order.session_id
        if invoice.state == 'draft':
            invoice.action_invoice_open()
        if (invoice and invoice.l10n_mx_edi_is_required()
                and invoice.l10n_mx_edi_pac_status != 'signed'):
            invoice._l10n_mx_edi_retry()
        if invoice:
            return invoice
        if session.state in ('closed', 'closing_control'):
            return order._get_invoice_from_close_session()
        return order._get_invoice_from_open_session()
