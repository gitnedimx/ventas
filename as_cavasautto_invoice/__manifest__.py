{
    "name": "Ahorasoft Generando Ventas",
    "summary": "Nucleo para Ventas y Facturacion",
    "category": "crm",
    "images": [],
    "version": "1.0.4",
    "application": True,
    "author": "Ahorasoft",
    "support": "soporte@ahorasoft.com",
    "website": "http://www.ahorasoft.com",
    "depends": [
        "crm",
        "sale",
        'base',
        'sale_management',
        'account',
        'l10n_mx_edi',
    ],
    'data': [
        'report/as_report_sale_order.xml',
        'report/as_report_invoice.xml',
    ],
    "auto_install": False,
    "installable": True,

}