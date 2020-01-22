{
    "name": "Generando Ventas",
    "summary": "Nucleo para Ventas",
    "category": "crm",
    "images": [],
    "version": "1.0.2",
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
    ],
    'data': [
        'report/as_report_sale_order.xml',
        'report/as_report_invoice.xml',
        'views/as_sale_order.xml',
    ],
    "auto_install": False,
    "installable": True,

}