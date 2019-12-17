# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Website Invoice Tickets",
    "summary": """
        Adds the ability of downloading, generating your e-invoices
        using your ticket number.
    """,
    "version": "12.0.1.0.0",
    "author": "Vauxoo",
    "category": "Website",
    "website": "http://www.vauxoo.com/",
    "license": "OEEL-1",
    "depends": [
        "l10n_mx_edi_pos",
        "portal",
        "website",
    ],
    "demo": [
        "demo/pos_order_demo.xml",
    ],
    "data": [
        "data/point_of_sale_data.xml",
        "views/assets.xml",
        "views/pos_order_view.xml",
        "views/templates.xml",
    ],
    "test": [],
    "js": [],
    "css": [],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
    "auto_install": False
}
