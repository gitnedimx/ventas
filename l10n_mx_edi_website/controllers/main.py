# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
from odoo import _, api, SUPERUSER_ID
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request, route
import odoo.http as http
from odoo.http import Controller
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class WebsiteCFDI(Controller):

    @route(
        ['/CFDI/<string:ticket_number>'],
        type='http', auth='public', website=True)
    def get_customer_cfdi(self, ticket_number=None):
        """Getting the invoice with the ticket_number sent and return the link
        to download pdf attached in the invoice"""
        values = {}
        try:
            with request.env.cr.savepoint():
                values = request.env['pos.order'].sudo().get_customer_cfdi(
                    ticket_number)
        # TODO - Check the correct exception
        except Exception as msg_error:
            _logger.error(msg_error)
            values.update(
                {'pac_error': _(
                    'Error at the moment to sign the invoice. '
                    'Please try again in few minutes'),
                 'ticket_number': ticket_number})
        values['action'] = ('/CFDI/report/pdf' if values.get('invoice') else
                            '/CFDI/validate_customer')
        return request.render('l10n_mx_edi_website.website_cfdi', values)

    @route(
        ['/CFDI/validate_customer'],
        type='http', auth='public', website=True)
    def validate_customer(self, **post):
        """Checking the values given to create or update a valid partner and
        generate the invoice"""
        values = request.params
        msg = ''
        vat = post.get('vat', False)
        email = post.get('email', False)
        if not post.get('email') or not post.get('vat'):
            msg = _('Fill all values on the form')
        valid_vat = request.env['res.partner'].check_vat_mx(
            post.get('vat'))

        msg = (valid_vat is False and not msg and
               _('Invalid vat. The format expected is ABC123456T1B.'))

        ticket_number = post.get('ticket_number',
                                 False) or values.get('ticket_number')
        try:
            with request.env.cr.savepoint():
                values = values if values.get('error') else request.env[
                    'pos.order'].sudo().update_partner(ticket_number, vat,
                                                       email)
        except Exception as msg_error:
            _logger.error(msg_error)
            values['error'] = _(
                'Error at the moment to sign the invoice. '
                'Please try again in few minutes')
        except BaseException as msg_error:
            _logger.error(msg_error)
            values['error'] = _(
                'Error at the moment to create the invoice. '
                'Please try again in few minutes')
        values['action'] = ('/CFDI/validate_customer'
                            if values.get('error') else
                            '/CFDI/report/pdf')
        return request.render(
            'l10n_mx_edi_website.website_cfdi', values)

    @route(
        ['/CFDI/pdf'],
        type='http', auth='public', website=True)
    def _get_electronic_document_pdf(self, **post):
        """Downloading the pdf attached to the invoice related with the
        ticket_number if This has one"""
        return self._download_attached_file(
            request.params.get('ticket_number'), 'pdf')

    @route(
        ['/CFDI/xml'],
        type='http', auth='public', website=True)
    def _get_electronic_document_xml(self, **post):
        """Downloading the XML attached to the invoice related with the
        ticket_number, if This has one"""
        return self._download_attached_file(
            request.params.get('ticket_number'), 'xml')

    def _download_attached_file(self, ticket, ftype='pdf'):
        """ Downloads the provided file type (PDF or XML) attached to the
            invoice related with the ticket_number, if This has one
        """
        vals = {'ticket_number': ticket}
        try:
            with request.env.cr.savepoint():
                vals = (
                    request.env['pos.order'].sudo().get_customer_cfdi(ticket))
        except (Exception, ZeroDivisionError):
            vals['pac_error'] = _(
                'Error at the moment to sign the invoice. '
                'Please try again in few minutes')
            return request.render(
                'l10n_mx_edi_website.website_cfdi', vals)
        except MailDeliveryException as e:
            _logger.error(e)
        with api.Environment.manage():
            env = api.Environment(request.env.cr, SUPERUSER_ID, {})
            inv = vals.get('invoice')
            fname = inv and '%s.%s' % (
                inv.l10n_mx_edi_cfdi_name.rstrip('.xml'), ftype)
            inv_attachment = inv and env['ir.attachment'].search(
                [('res_model', '=', 'account.invoice'),
                 ('res_id', '=', inv.id),
                 ('datas_fname', '=', fname),
                 ], limit=1)
            if (inv and inv.l10n_mx_edi_pac_status == 'signed' and
                    not inv_attachment and ftype == 'pdf'):
                report_info = inv.invoice_print()
                report = env['ir.actions.report']._get_report_from_name(
                    report_info['report_name'])
                report.render(inv.ids)[0]
                inv_attachment = inv and env['ir.attachment'].search(
                    [('res_model', '=', 'account.invoice'),
                     ('res_id', '=', inv.id),
                     ('datas_fname', '=', fname),
                     ], limit=1)

            if inv_attachment:
                status, headers, content = request.env[
                    'ir.http'].binary_content(id=inv_attachment.id, env=env,
                                              download=True)
                image_base64 = base64.b64decode(content)
                headers.append(('Content-Length', len(image_base64)))
                response = request.make_response(image_base64, headers)
                response.status_code = status
                return response
        vals.update(
            {'action': '/CFDI/validate_customer',
             'error': 'The invoice selected does not have attachments'}
        )
        return request.render(
            'l10n_mx_edi_website.website_cfdi', vals)


class CAuthSignupHome(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        """Overwritten to force an email validation when the new user wants to
        be related with a partner already created with possible orders
        related
        """
        res = super(CAuthSignupHome, self).web_auth_signup(*args, **kw)
        if not res.qcontext.get('vat'):
            return res
        error = res.qcontext.get('error')
        msg = _('We sent you an email to complete the registry.')
        if error:
            msg = '%s %s' % (msg, _(
                'If you have not received this mail probably it is %s') % (
                    error))
        vals = {'message': msg, 'login': res.qcontext.get('login')}
        return request.render('web.login', vals)

    def _signup_with_values(self, token, values):
        """Overwritten to add the vat in values used to create the new user"""
        values['vat'] = request.params.get('vat', '')
        return super(CAuthSignupHome, self)._signup_with_values(token, values)
