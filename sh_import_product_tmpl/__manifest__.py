# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Import Product Template from CSV/Excel file",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "info@softhealer.com",    
    "category": "Product",
    "summary": "This module useful to import product template from csv/excel.",
    "description": """
    
 This module useful to import product template from csv/excel. 
 
 

                    """,    
    "version":"12.0.2",
    "depends" : ["base","sale","sale_management","sh_message","product","stock","account"],
    "application" : True,
    "data" : ['security/import_product_tmpl_security.xml',

            'wizard/import_product_tmpl_wizard.xml',
            'views/sale_view.xml',
            ],         
    'external_dependencies' : {
        'python' : ['xlrd'],
    },                  
    "images": ["static/description/background.png",],              
    "auto_install":False,
    "installable" : True,
    "price": 25,
    "currency": "EUR"   
}
