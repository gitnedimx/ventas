# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Advance Credit Check Rules',
    'version': '1.0',
    'summary': 'Allows to configure advance credit check rules and apply on customer',
    'sequence': 21,
    'description': """
        Allows to configure advance credit check rules and apply on customer
        
        
        credit
credit limit
customer credit
customer credit limit
customer due
past due
credit restriction
payment
payment credit
payment credit limit
customer payment
customer payment credit
customer payment credit limit
credit score
customer credit score
advance credit
advance credit limit
advance customer credit
advance customer credit limit
borrower
withdraw
credit account
payment term
accounting
taxation
audit
account
tax
finance
financial management
letter of credit
leverage
balance
line of credit
bank line
customer
customer payment overdue
overdue customer payment
customer overdue payment reminder
customer overdue payment followup
due days
payment due
due payment
scheduler
analysis
followup analysis
Accounting & Auditing Terms
accounting concepts
marginal benefit
asset
revenue
buyer
amount due
due amount
demand
cash
cash on delivery
deferred payment
period
duration
provision
cash flow
enterpreneur
monitoring
sale
feedback
requirement
effectiveness
following
auditing
management
contract management
    """,
    'category': 'Sales',
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'images': [
        'static/description/main_screen.jpg'
    ],
    'depends': ['payment_credit_limit'],
    'data': [
            'data/credit_code_data.xml',
            'security/ir.model.access.csv',
            'views/partner_view.xml',
            'views/credit_code_view.xml',
    ],
    'demo': [],
    'price': 60,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
