# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon


class TestTicketInvoicing(TestPointOfSaleCommon):

    def setUp(self):
        super(TestTicketInvoicing, self).setUp()
        self.order_obj = self.env['pos.order']
        self.partner_obj = self.env['res.partner']
        self.company = self.env.ref('base.main_company')
        self.led_lamp.l10n_mx_edi_code_sat_id = self.ref(
            "l10n_mx_edi.prod_code_sat_50402500")
        self.fiscal_position = self.env.ref(
            'l10n_mx.1_account_fiscal_position_601_fr')
        self.fiscal_position.l10n_mx_edi_code = '601'
        self.partner1.property_account_position_id = self.fiscal_position
        self.tax_positive = self.env['account.tax'].search([
            ('name', '=', 'IVA(16%) VENTAS')
            ], limit=1)
        self.tax_positive.l10n_mx_cfdi_tax_type = 'Tasa'
        self.led_lamp.write({
            'l10n_mx_edi_code_sat_id': self.ref(
                "l10n_mx_edi.prod_code_sat_39112102"),
            'taxes_id': [(6, 0, self.tax_positive.ids)],
        })
        self.fiscal_position = self.env.ref(
            'l10n_mx.1_account_fiscal_position_601_fr')
        self.fiscal_position.l10n_mx_edi_code = '601'
        self.partner1.property_account_position_id = self.fiscal_position
        self.vat_valid = 'VA&111017CG9'
        self.partner4.vat = self.vat_valid
        self.known_email = 'info(at)vauxoo.com'
        self.unknown_email = 'somebody@vauxoo.com'
        self.vat_new = 'ACI010425FU7'
        self.unregistered_email = 'somebody-not@vauxoo.com'
        self.pos_config.journal_ids.profit_account_id = self.env.ref(
            'l10n_mx.1_cuenta701_01')
        self.create_orders()

    def create_orders(self):
        """Simulation of sales coming from the interface,
        even after closing the session
        """
        fromproduct = object()

        def compute_tax(product, price, taxes=fromproduct, qty=1):
            if taxes is fromproduct:
                taxes = product.taxes_id
            currency = self.pos_config.pricelist_id.currency_id
            taxes = taxes.compute_all(
                price, currency, qty, product=product)['taxes']
            untax = price * qty
            return untax, sum(tax.get('amount', 0.0) for tax in taxes)

        # I click on create a new session button
        self.pos_config.open_session_cb()

        current_session = self.pos_config.current_session_id

        untax, atax = compute_tax(self.led_lamp, 0.9)
        without_partner_order = {
            'data': {
                'amount_paid': untax + atax,
                'amount_return': 0,
                'amount_tax': atax,
                'amount_total': untax + atax,
                'creation_date': fields.Datetime.now(),
                'fiscal_position_id': False,
                'lines': [[0, 0,
                           {'discount': 0, 'id': 42, 'pack_lot_ids': [],
                            'price_unit': 0.9,
                            'price_subtotal': 0.9,
                            'price_subtotal_incl': 0.9,
                            'product_id': self.led_lamp.id,
                            'qty': 1,
                            'tax_ids': [(6, 0,
                                         self.led_lamp.taxes_id.ids)]}]],
                'name': 'Order 10042-003-0014',
                'partner_id': False,
                'pricelist_id':
                    self.partner1.property_product_pricelist.id,
                'pos_session_id': current_session.id,
                'sequence_number': 2,
                'ticket_number': '22345',
                'statement_ids': [[0, 0,
                                   {'account_id':
                                    (self.env.user.partner_id.
                                     property_account_receivable_id.id),
                                    'amount': untax + atax,
                                    'journal_id':
                                    self.pos_config.journal_ids[0].id,
                                    'name': fields.Datetime.now(),
                                    'statement_id':
                                    current_session.statement_ids[0].id}]],
                'uid': '10042-003-0014',
                'user_id': self.env.uid},
            'id': '10042-003-0014',
            'to_invoice': False}

        # I create an order on an open session
        without_ids = self.PosOrder.create_from_ui([without_partner_order])
        self.ticket_no_partner = self.order_obj.browse(without_ids)

        without_partner_order['id'] = '10042-003-0015'
        without_partner_order['data'].update(
            {'partner_id': self.partner4.id,
             'ticket_number': '223456',
             'name': 'Order 10042-003-0015'})
        with_ids = self.PosOrder.create_from_ui([without_partner_order])
        self.not_invoiced_valid_partner = self.order_obj.browse(with_ids)

        without_partner_order.update({
            'id': '10042-003-0016',
            'to_invoice': True,
        })
        without_partner_order['data'].update(
            {'ticket_number': '223457',
             'name': 'Order 10042-003-0016'})

        invoiced_ids = self.PosOrder.create_from_ui([without_partner_order])
        self.invoiced_ticket = self.order_obj.browse(invoiced_ids)

    def test_001_invoiced_ticket(self):
        """Tests case: a ticket has already an invoice.
        """
        res = self.order_obj.get_customer_cfdi(
            self.invoiced_ticket.l10n_mx_edi_ticket_number)
        self.assertEqual(res.get('invoice'), self.invoiced_ticket.invoice_id)

    def test_002_not_invoiced_valid_partner(self):
        """Test case: A ticket has partner and the data of the partner is
        correctly set, so an invoice is created and returned.
        """
        res = self.order_obj.get_customer_cfdi(
            self.not_invoiced_valid_partner.l10n_mx_edi_ticket_number)
        invoice = res.get('invoice')
        self.assertEqual(invoice, self.not_invoiced_valid_partner.invoice_id)

    def test_003_no_partner(self):
        """Test case: A ticket has no partner, an error must be returned on the
        partner key.
        """
        res = self.order_obj.get_customer_cfdi(
            self.ticket_no_partner.l10n_mx_edi_ticket_number)
        self.assertEqual(res.get('partner'), 'No partner')

    def test_004_invoice_by_vat(self):
        """Test case: A ticket has no partner but customer data already in the
        system.
        """
        res = self.order_obj.update_partner(
            self.ticket_no_partner.l10n_mx_edi_ticket_number,
            self.vat_valid, self.known_email)
        self.assertEqual(res.get('invoice'), self.ticket_no_partner.invoice_id)

    def test_005_invoice_by_vat(self):
        """Test case: A ticket has no partner but customer data already in the
        system but email provided is different from the one found in the
        database.
        """
        res = self.order_obj.update_partner(
            self.ticket_no_partner.l10n_mx_edi_ticket_number,
            self.vat_valid, self.unknown_email)
        self.assertEqual(res.get('invoice'), self.ticket_no_partner.invoice_id)

    def test_006_invoice_new_customer(self):
        """Test case: A ticket has no partner and there is no data matching
        on any partner with the one given on the form.
        """
        res = self.order_obj.update_partner(
            self.ticket_no_partner.l10n_mx_edi_ticket_number,
            self.vat_new, self.unregistered_email)
        new_invoice = res.get('invoice')
        new_partner = self.partner_obj.search(
            [('email', '=', 'somebody-not@vauxoo.com'),
             ('vat', '=', 'ACI010425FU7')])
        self.assertEqual(new_invoice.partner_id, new_partner)

    def test_007_invoice_incomplete_data(self):
        """Test case: A ticket has no partner but the data supplied on the form
        is incomplete and there is no matching record on the database.
        """
        res = self.order_obj.update_partner(
            self.ticket_no_partner.l10n_mx_edi_ticket_number,
            email=self.unregistered_email)
        self.assertEqual(res.get('vat'), 'Required')
        self.assertTrue(res.get('error'))

    def test_008_invoice_sale(self):
        """Test case: a ticket number is given and the customer data on the
        order is valid to be invoiced.
        """
        ticket_number = (
            self.not_invoiced_valid_partner.l10n_mx_edi_ticket_number)
        res = self.order_obj.invoice_sale(ticket_number)
        self.assertTrue(res)

    def test_009_invoice_session_closed(self):
        """Test case: a ticket number is given, but the customer completes the
        form after the session has been closed
        """
        ticket_number = (
            self.not_invoiced_valid_partner.l10n_mx_edi_ticket_number)
        session = self.pos_order_session0
        session.action_pos_session_closing_control()
        self.assertEqual(session.l10n_mx_edi_pac_status, "signed",
                         session.message_ids.mapped('body'))
        invoice = self.order_obj.invoice_sale(ticket_number)
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        self.assertEqual(invoice.state, 'paid', 'Invoice should be paid')

    def test_010_misconfigured_and_retry(self):
        """Test case: The instance is misconfigured when closing the session,
        then configuration is fixed and the session is re-signed
        """
        # Misconfigure the instance and close, so SAT signing process fails
        session = self.pos_order_session0
        vat = self.company.vat
        self.company.vat = False
        session.action_pos_session_closing_control()
        self.assertEqual(session.l10n_mx_edi_pac_status, "retry",
                         session.message_ids.mapped('body'))

        # Re-configure instance and retry the signing process
        self.company.vat = vat
        session._l10n_mx_edi_retry()
        self.assertEqual(session.l10n_mx_edi_pac_status, "signed",
                         session.message_ids.mapped('body'))
