
.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :alt: License: LGPL-3

Mexican POS Management System
=============================

When is generated a new sale from point of sale, the user have three options
before to validate the order:

1. Not assign customer in the sale.
2. Assign a customer in the sale.
3. Assign customer in the sale, and generate the invoice.

.. image:: l10n_mx_edi_pos/static/src/img/cases_pos.png

This module add a new button that allow generate the XML files related with
the session, after that it is closed.

The XML file take the data from all orders related with the session depending
in wich case is each order.

**What makes this module depending on the case?**

**CASE 1:**

With all orders that have not partner assigned, is generated one XML with the
generic partner, and is sent to sign with the PAC assigned in the session
journal.

The resultant XML is attached in the section.

**CASE 2:**

For this case, all the orders that have assigned the customer but are not
invoiced are splitted in two groups:

- Group 1
   All orders whose address partner have configured
    - Street
    - City
    - State
    - Country
    - Zip

- Group 2
  The rest of orders that have partner, but the addess is not completed.

All the orders in group 1 are sent to generate the invoice with the same
action that Odoo provide.

With all orders in group 2, is generated one XML for the generic partner, and
is sent to sign with the PAC assigned in the session journal.

The resultant XML is attached in the section.

**CASE 3:**

In this case like the orders already have an invoice, in the invoice is
generated directly the XML. In this module not are afected this orders.


Also is added the option to validate all invoices generated in the session
after to close it.

.. contents::

Installation
============

To install this module, you need to:

- Not special pre-installation is required, just install as a regular Odoo
  module:

  - Download this module from `Vauxoo/mexico
    <https://github.com/vauxoo/mexico>`_
  - Add the repository folder into your odoo addons-path.
  - Go to ``Settings > Module list`` search for the current name and click in
    ``Install`` button.

Configuration
=============

To configure this module, you need to:

* There is not special configuration for this module.

Bug Tracker
===========

Bugs are tracked on
`GitHub Issues <https://github.com/Vauxoo/mexico/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback
`here <https://github.com/Vauxoo/mexico/issues/new?body=module:%20
l10n_mx_edi_pos%0Aversion:%20
8.0.2.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_

Credits
=======

**Contributors**

* Nhomar Hernandez <nhomar@vauxoo.com> (Planner/Auditor)
* Luis Torres <luis_t@vauxoo.com> (Developer)

Maintainer
==========

.. image:: https://s3.amazonaws.com/s3.vauxoo.com/description_logo.png
   :alt: Vauxoo
