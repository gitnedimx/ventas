# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name': "Print POS Session Report",
    'version': "12.0.0.1",
    'summary': "",
    'category': 'Point Of Sale',
    "license": "AGPL-3",
    'description': """
    """,
    'author': "Sitaram",
    'website':"sitaramsolutions.com",
    'depends': ['base', 'point_of_sale'],
    'data': [
        'reports/pos_report.xml',
'reports/pos_session_report_template.xml'
    ],
    'demo': [],
    'images':['static/description/banner.png'],
    'live_test_url':'https://youtu.be/xYuOpF4aZis',
    'installable': True,
    'application': False,
    'auto_install': False,
}
