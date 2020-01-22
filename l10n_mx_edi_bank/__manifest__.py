# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Mexican Localization Banks",
    "summary": """
        Mexican Banks data, ABM Code & CLABE number for Banks Accounts.
    """,
    "version": "12.0.1.0.0",
    "author": "Vauxoo",
    "category": "Accounting",
    "website": "http://www.vauxoo.com/",
    "license": "OEEL-1",
    "depends": [
        "l10n_mx_edi",
    ],
    "data": [
        "data/res_bank_data.xml",
        "views/res_bank_view.xml",
    ],
    "installable": True,
    "auto_install": False
}
