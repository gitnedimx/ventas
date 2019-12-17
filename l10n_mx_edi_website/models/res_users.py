# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import datetime
import hashlib
from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        """Overwritten to verify the vat used to create the new user

        If the vat used belongs to another partner, an email of verification is
        sent to the email register in the main partner, this is to validate the
        access to the new user on orders created with the related partner.

        If a partner is found with the vat used, the password used in the form
        is not valid any more, it will need to be created from the link sent to
        the partner.
        """
        vat = values.get('vat')
        login = values.get('login')
        partner_obj = self.env['res.partner']
        commercial = vat and partner_obj.search(
            ['|', '&', '|',
             ('email', '!=', False),
             ('email', 'ilike', login),
             ('vat', '=', vat),
             ('commercial_partner_id.vat', '=', vat)],
            limit=1)

        if not commercial:
            return super(ResUsers, self)._signup_create_user(values)
        uemail = values.get('email')
        email = commercial.email.split(';')[0] or ''
        contact = partner_obj.create({
            'name': values.get('name'),
            'email': commercial.email,
            'parent_id': commercial.id,
        })
        values['partner_id'] = contact.id
        values.update({
            'email': email,
        })
        new_user = super(ResUsers, self)._signup_create_user(values)
        new_user.action_reset_password()
        passwd = hashlib.sha256('%s-%s-%s' % (
            datetime.now(),
            new_user.id,
            new_user.login)).hexdigest()
        old_val = {
            'email': '%s;%s' % (email, uemail),
            'password': passwd,
        }
        new_user.write(old_val)
        return new_user
