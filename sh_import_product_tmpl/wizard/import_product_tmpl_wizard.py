# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
import csv
import base64
import io as StringIO
import xlrd
from odoo.tools import ustr
import requests
import codecs

class import_product_tmpl_wizard(models.TransientModel):
    _name="import.product.tmpl.wizard"
    _description = "Import product template wizard"        

    import_type = fields.Selection([
        ('csv','CSV File'),
        ('excel','Excel File')
        ], default="csv", string="Import File Type", required=True)
    file = fields.Binary(string="File",required=True)
    method = fields.Selection([
        ('create','Create Product'),
        ('write','Create or Update Product')
        ], default = "create", string = "Method", required = True)
    
    product_update_by = fields.Selection([
        ('barcode','Barcode'),
        ('int_ref','Internal Reference'),
        ], default = 'barcode', string = "Product Update By", required = True)
    
    @api.multi
    def show_success_msg(self,counter,skipped_line_no):
        
        #to close the current active wizard        
        action = self.env.ref('sh_import_product_tmpl.sh_import_product_tmpl_action').read()[0]
        action = {'type': 'ir.actions.act_window_close'} 
        
        #open the new success message box    
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False                                   
        context = dict(self._context or {})
        dic_msg = str(counter) + " Records imported successfully"
        if skipped_line_no:
            dic_msg = dic_msg + "\nNote:"
        for k,v in skipped_line_no.items():
            dic_msg = dic_msg + "\nRow No " + k + " " + v + " "
        context['message'] = dic_msg   
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
            }   

    
    @api.multi
    def import_product_tmpl_apply(self):

        product_tmpl_obj = self.env['product.template']
        #perform import lead
        if self and self.file:
            #For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                try:
                    file = str(base64.decodestring(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header=True
                    
                    for row in myreader:
                        try:
                            if skip_header:
                                skip_header=False
                                counter = counter + 1
                                continue
                            if row[0].strip() not in (None,""): 
                                
                                can_be_sold = True
                                if row[1].strip() == 'FALSE':
                                    can_be_sold = False
                                
                                can_be_purchased = True
                                if row[2].strip() == 'FALSE':
                                    can_be_purchased = False
                                    
                                
                                product_type = 'consu'
                                if row[3].strip() == 'Service':
                                    product_type = 'service'
                                elif row[3].strip() == 'Stockable Product':
                                    product_type = 'product'
                                    
                                categ_id = False
                                if row[4].strip() in (None,""):
                                    search_category = self.env['product.category'].search([('complete_name','=','All')], limit = 1)
                                    if search_category:
                                        categ_id = search_category.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Category - All not found. "                                         
                                        counter = counter + 1
                                        continue
                                else:
                                    search_category = self.env['product.category'].search([('complete_name','=',row[4].strip())], limit = 1)
                                    if search_category:
                                        categ_id = search_category.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Category not found. " 
                                        counter = counter + 1
                                        continue
 
                                uom_id = False
                                if row[9].strip() in (None,""):
                                    search_uom = self.env['uom.uom'].search([('name','=','Unit(s)')], limit = 1)
                                    if search_uom:
                                        uom_id = search_uom.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Unit of Measure - Unit(s) not found. "                                         
                                        counter = counter + 1
                                        continue                                        
                                else:
                                    search_uom = self.env['uom.uom'].search([('name','=',row[9].strip())], limit = 1)
                                    if search_uom:
                                        uom_id = search_uom.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Unit of Measure not found. "                                         
                                        counter = counter + 1
                                        continue   
                                                                        
                                uom_po_id = False
                                if row[10].strip() in (None,""):
                                    search_uom_po = self.env['uom.uom'].search([('name','=','Unit(s)')], limit = 1)
                                    if search_uom_po:
                                        uom_po_id = search_uom_po.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Purchase Unit of Measure - Unit(s) not found. "                                         
                                        counter = counter + 1
                                        continue                                        
                                else:
                                    search_uom_po = self.env['uom.uom'].search([('name','=',row[10].strip())], limit = 1)
                                    if search_uom_po:
                                        uom_po_id = search_uom_po.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Purchase Unit of Measure not found. "                                         
                                        counter = counter + 1
                                        continue   
                                
                                customer_taxes_ids_list = []
                                some_taxes_not_found = False
                                if row[13].strip() not in (None,""):
                                    for x in row[13].split(','):
                                        x = x.strip()
                                        if x != '':
                                            search_customer_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                            if search_customer_tax:
                                                customer_taxes_ids_list.append(search_customer_tax.id)
                                            else:
                                                some_taxes_not_found = True
                                                skipped_line_no[str(counter)]= " - Customer Taxes " + x +  " not found. "                                                 
                                                break
                                
                                if some_taxes_not_found:
                                    counter = counter + 1                                    
                                    continue
                                
                                vendor_taxes_ids_list = []

                                
                                some_taxes_not_found = False
                                if row[14].strip() not in (None,""):
                                    for x in row[14].split(','):
                                        x = x.strip()
                                        if x != '':
                                            search_vendor_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                            if search_vendor_tax:
                                                vendor_taxes_ids_list.append(search_vendor_tax.id)
                                            else:
                                                some_taxes_not_found = True
                                                skipped_line_no[str(counter)]= " - Vendor Taxes " + x +  " not found. "                                                 
                                                break
                                
               
                                if some_taxes_not_found:
                                    counter = counter + 1                                    
                                    continue
                                
                                invoicing_policy = 'order'
                                if row[15].strip() == 'Delivered quantities':
                                    invoicing_policy = 'delivery'
                                                                      
                                                           
                                vals={
                                    'name'              : row[0].strip(),
                                    'sale_ok'           : can_be_sold,
                                    'purchase_ok'       : can_be_purchased,
                                    'type'              : product_type,
                                    'categ_id'          : categ_id,
                                    'list_price'        : row[7],
                                    'standard_price'    : row[8],
                                    'uom_id'            : uom_id,
                                    'uom_po_id'         : uom_po_id,
                                    'weight'            : row[11],
                                    'volume'            : row[12],
                                    'taxes_id'          : [(6, 0, customer_taxes_ids_list)],
                                    'supplier_taxes_id' : [(6, 0, vendor_taxes_ids_list)],
                                    'invoice_policy'    : invoicing_policy,
                                    'description_sale'  : row[16],
                                    }
                                
                                if row[6].strip() not in (None,""):
                                    barcode = row[6].strip()
                                    vals.update({'barcode':barcode})
                                                            
                                if row[5].strip() not in (None,""):
                                    default_code = row[5].strip()
                                    vals.update({'default_code':default_code})
                                
                                if row[18].strip() not in (None,""):
                                    image_path = row[18].strip()
                                    if "http://" in image_path or "https://" in image_path:
                                        try:
                                            r = requests.get(image_path)
                                            if r and r.content:
                                                image_base64 = base64.encodestring(r.content) 
                                                vals.update({'image_medium': image_base64})
                                            else:
                                                skipped_line_no[str(counter)] = " - URL not correct or check your image size. "                                            
                                                counter = counter + 1                                                
                                                continue
                                        except Exception as e:
                                            skipped_line_no[str(counter)] = " - URL not correct or check your image size " + ustr(e)   
                                            counter = counter + 1 
                                            continue                                              
                                        
                                    else:
                                        try:
                                            with open(image_path, 'rb') as image:
                                                image.seek(0)
                                                binary_data = image.read()
                                                image_base64 = codecs.encode(binary_data, 'base64')     
                                                if image_base64:
                                                    vals.update({'image_medium': image_base64})
                                                else:
                                                    skipped_line_no[str(counter)] = " - Could not find the image or please make sure it is accessible to this user. "                                            
                                                    counter = counter + 1                                                
                                                    continue                                                                       
                                        except Exception as e:
                                            skipped_line_no[str(counter)] = " - Could not find the image or please make sure it is accessible to this user " + ustr(e)   
                                            counter = counter + 1 
                                            continue                                                                                                                              
                                                                               
                                        
                                created_product_tmpl = False
                                if self.method == 'create':
                                    if row[6].strip() in (None,""):
                                        created_product_tmpl = product_tmpl_obj.create(vals)
                                        counter = counter + 1                                        
                                    else:
                                        search_product_tmpl = product_tmpl_obj.search([('barcode','=',row[6].strip())],limit = 1)
                                        if search_product_tmpl:
                                            skipped_line_no[str(counter)] = " - Barcode already exist. "
                                            counter = counter + 1
                                            continue
                                        else:
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1
                                elif self.method == 'write' and self.product_update_by == 'barcode':
                                    if row[6].strip() in (None,""):
                                        created_product_tmpl = product_tmpl_obj.create(vals)
                                        counter = counter + 1                                    
                                    else:
                                        search_product_tmpl = product_tmpl_obj.search([('barcode','=',row[6].strip())],limit = 1)
                                        if search_product_tmpl:
                                            created_product_tmpl = search_product_tmpl
                                            search_product_tmpl.write(vals)
                                            counter = counter + 1
                                        else:
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1
                                elif self.method == 'write' and self.product_update_by == 'int_ref':
                                    search_product_tmpl = product_tmpl_obj.search([('default_code','=',row[5].strip())],limit = 1)
                                    if search_product_tmpl:
                                        if row[6].strip() in (None,""):
                                            created_product_tmpl = search_product_tmpl
                                            search_product_tmpl.write(vals)
                                            counter = counter + 1
                                        else:
                                            search_product_tmpl_bar = product_tmpl_obj.search([('barcode','=',row[6].strip())],limit = 1)
                                            if search_product_tmpl_bar:
                                                skipped_line_no[str(counter)] = " - Barcode already exist. "
                                                counter = counter + 1
                                                continue                                            
                                            else:
                                                created_product_tmpl = search_product_tmpl
                                                search_product_tmpl.write(vals)
                                                counter = counter + 1
                                    else:
                                        if row[6].strip() in (None,""):
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1  
                                        else:
                                            search_product_tmpl_bar = product_tmpl_obj.search([('barcode','=',row[6].strip())],limit = 1)
                                            if search_product_tmpl_bar:
                                                skipped_line_no[str(counter)] = " - Barcode already exist. "
                                                counter = counter + 1
                                                continue                                            
                                            else:
                                                created_product_tmpl = product_tmpl_obj.create(vals)
                                                counter = counter + 1                                                                           
                                  
                                if created_product_tmpl and created_product_tmpl.product_variant_id and created_product_tmpl.type == 'product' and row[17] != '':
                                    stock_vals = {'product_tmpl_id' : created_product_tmpl.id,
                                                  'new_quantity'    : row[17], 
                                                  'product_id'      : created_product_tmpl.product_variant_id.id
                                                  }
                                    created_qty_on_hand = self.env['stock.change.product.qty'].create(stock_vals)
                                    if created_qty_on_hand:
                                        created_qty_on_hand.change_product_qty()                                    
                                    
                                    
                            else:
                                skipped_line_no[str(counter)]=" - Name is empty. "  
                                counter = counter + 1      
                        except Exception as e:
                            skipped_line_no[str(counter)]=" - Value is not valid. " + ustr(e)   
                            counter = counter + 1 
                            continue          
                            
                except Exception:
                    raise UserError(_("Sorry, Your csv file does not match with our format"))
                
                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(completed_records, skipped_line_no)
                    return res

            
            #For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}                  
                try:
                    wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
                    sheet = wb.sheet_by_index(0)     
                    skip_header = True    
                    for row in range(sheet.nrows):
                        try:
                            if skip_header:
                                skip_header = False
                                counter = counter + 1
                                continue
                            
                            if sheet.cell(row,0).value.strip()  not in (None,""): 
                                
                                can_be_sold = True
                                if sheet.cell(row,1).value.strip() == 'FALSE':
                                    can_be_sold = False
                                
                                can_be_purchased = True
                                if sheet.cell(row,2).value.strip() == 'FALSE':
                                    can_be_purchased = False
                                    
                                
                                product_type = 'consu'
                                if sheet.cell(row,3).value.strip() == 'Service':
                                    product_type = 'service'
                                elif sheet.cell(row,3).value.strip() == 'Stockable Product':
                                    product_type = 'product'
                                    
                                categ_id = False
                                if sheet.cell(row,4).value.strip() in (None,""):
                                    search_category = self.env['product.category'].search([('complete_name','=','All')], limit = 1)
                                    if search_category:
                                        categ_id = search_category.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Category - All not found. "                                         
                                        counter = counter + 1
                                        continue
                                else:
                                    search_category = self.env['product.category'].search([('complete_name','=',sheet.cell(row,4).value.strip())], limit = 1)
                                    if search_category:
                                        categ_id = search_category.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Category not found. " 
                                        counter = counter + 1
                                        continue
 
                                uom_id = False
                                if sheet.cell(row,9).value.strip() in (None,""):
                                    search_uom = self.env['uom.uom'].search([('name','=','Unit(s)')], limit = 1)
                                    if search_uom:
                                        uom_id = search_uom.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Unit of Measure - Unit(s) not found. "                                         
                                        counter = counter + 1
                                        continue                                        
                                else:
                                    search_uom = self.env['uom.uom'].search([('name','=',sheet.cell(row,9).value.strip())], limit = 1)
                                    if search_uom:
                                        uom_id = search_uom.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Unit of Measure not found. "                                         
                                        counter = counter + 1
                                        continue   
                                                                        
                                uom_po_id = False
                                if sheet.cell(row,10).value.strip() in (None,""):
                                    search_uom_po = self.env['uom.uom'].search([('name','=','Unit(s)')], limit = 1)
                                    if search_uom_po:
                                        uom_po_id = search_uom_po.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Purchase Unit of Measure - Unit(s) not found. "                                         
                                        counter = counter + 1
                                        continue                                        
                                else:
                                    search_uom_po = self.env['uom.uom'].search([('name','=',sheet.cell(row,10).value.strip())], limit = 1)
                                    if search_uom_po:
                                        uom_po_id = search_uom_po.id
                                    else:
                                        skipped_line_no[str(counter)] = " - Purchase Unit of Measure not found. "                                         
                                        counter = counter + 1
                                        continue   
                                customer_taxes_ids_list = []
                                some_taxes_not_found = False
                                if sheet.cell(row,13).value.strip() not in (None,""):
                                    for x in sheet.cell(row,13).value.split(','):
                                        x = x.strip()
                                        if x != '':
                                            search_customer_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                            if search_customer_tax:
                                                customer_taxes_ids_list.append(search_customer_tax.id)
                                            else:
                                                some_taxes_not_found = True
                                                skipped_line_no[str(counter)]= " - Customer Taxes " + x +  " not found. "                                                 
                                                break
                                
                                if some_taxes_not_found:
                                    counter = counter + 1                                    
                                    continue
                                
                                vendor_taxes_ids_list = []
                                some_taxes_not_found = False
                                if sheet.cell(row,14).value.strip() not in (None,""):
                                    for x in sheet.cell(row,14).value.split(','):
                                        x = x.strip()
                                        if x != '':
                                            search_vendor_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                            if search_vendor_tax:
                                                vendor_taxes_ids_list.append(search_vendor_tax.id)
                                            else:
                                                some_taxes_not_found = True
                                                skipped_line_no[str(counter)]= " - Vendor Taxes " + x +  " not found. "                                                 
                                                break
                                
                                if some_taxes_not_found:
                                    counter = counter + 1                                    
                                    continue
                                invoicing_policy = 'order'
                                if sheet.cell(row,15).value.strip() == 'Delivered quantities':
                                    invoicing_policy = 'delivery'
                                                                      
                                                           
                                vals={
                                    'name'              : sheet.cell(row,0).value.strip(),
                                    'sale_ok'           : can_be_sold,
                                    'purchase_ok'       : can_be_purchased,
                                    'type'              : product_type,
                                    'categ_id'          : categ_id,
                                    'list_price'        : sheet.cell(row,7).value,
                                    'standard_price'    : sheet.cell(row,8).value,
                                    'uom_id'            : uom_id,
                                    'uom_po_id'         : uom_po_id,
                                    'weight'            : sheet.cell(row,11).value,
                                    'volume'            : sheet.cell(row,12).value,
                                    'taxes_id'          : [(6, 0, customer_taxes_ids_list)],
                                    'supplier_taxes_id' : [(6, 0, vendor_taxes_ids_list)],
                                    'invoice_policy'    : invoicing_policy,
                                    'description_sale'  : sheet.cell(row,16).value,
                                    }
                                if sheet.cell(row,6).value not in (None,""):
                                    barcode = sheet.cell(row,6).value
                                    vals.update({'barcode':barcode})
                                                            
                                if sheet.cell(row,5).value not in (None,""):
                                    default_code = sheet.cell(row,5).value
                                    vals.update({'default_code':default_code})
                                
                                if sheet.cell(row,18).value.strip() not in (None,""):
                                    image_path = sheet.cell(row,18).value.strip()
                                    if "http://" in image_path or "https://" in image_path:
                                        try:
                                            r = requests.get(image_path)
                                            if r and r.content:
                                                image_base64 = base64.encodestring(r.content) 
                                                vals.update({'image_medium': image_base64})
                                            else:
                                                skipped_line_no[str(counter)] = " - URL not correct or check your image size. "                                            
                                                counter = counter + 1                                                
                                                continue
                                        except Exception as e:
                                            skipped_line_no[str(counter)] = " - URL not correct or check your image size " + ustr(e)   
                                            counter = counter + 1 
                                            continue                                              
                                        
                                    else:
                                        try:
                                            with open(image_path, 'rb') as image:
                                                image.seek(0)
                                                binary_data = image.read()
                                                image_base64 = codecs.encode(binary_data, 'base64')     
                                                if image_base64:
                                                    vals.update({'image_medium': image_base64})
                                                else:
                                                    skipped_line_no[str(counter)] = " - Could not find the image or please make sure it is accessible to this user. "                                            
                                                    counter = counter + 1                                                
                                                    continue                                                                       
                                        except Exception as e:
                                            skipped_line_no[str(counter)] = " - Could not find the image or please make sure it is accessible to this user " + ustr(e)   
                                            counter = counter + 1 
                                            continue                                                                                                                                 
                                                                               
                                        
                                created_product_tmpl = False
                                if self.method == 'create':
                                    if sheet.cell(row,6).value in (None,""):
                                        created_product_tmpl = product_tmpl_obj.create(vals)
                                        counter = counter + 1                                        
                                    else:
                                        search_product_tmpl = product_tmpl_obj.search([('barcode','=',sheet.cell(row,6).value)],limit = 1)
                                        if search_product_tmpl:
                                            skipped_line_no[str(counter)] = " - Barcode already exist. "
                                            counter = counter + 1
                                            continue
                                        else:
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1
                                elif self.method == 'write' and self.product_update_by == 'barcode':
                                    if sheet.cell(row,6).value in (None,""):
                                        created_product_tmpl = product_tmpl_obj.create(vals)
                                        counter = counter + 1                                    
                                    else:
                                        search_product_tmpl = product_tmpl_obj.search([('barcode','=',sheet.cell(row,6).value)],limit = 1)
                                        if search_product_tmpl:
                                            created_product_tmpl = search_product_tmpl
                                            search_product_tmpl.write(vals)
                                            counter = counter + 1
                                        else:
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1
                                elif self.method == 'write' and self.product_update_by == 'int_ref':
                                    search_product_tmpl = product_tmpl_obj.search([('default_code','=',sheet.cell(row,5).value)],limit = 1)
                                    if search_product_tmpl:
                                        if sheet.cell(row,6).value in (None,""):
                                            created_product_tmpl = search_product_tmpl
                                            search_product_tmpl.write(vals)
                                            counter = counter + 1
                                        else:
                                            search_product_tmpl_bar = product_tmpl_obj.search([('barcode','=',sheet.cell(row,6).value)],limit = 1)
                                            if search_product_tmpl_bar:
                                                skipped_line_no[str(counter)] = " - Barcode already exist. "
                                                counter = counter + 1
                                                continue                                            
                                            else:
                                                created_product_tmpl = search_product_tmpl
                                                search_product_tmpl.write(vals)
                                                counter = counter + 1
                                    else:
                                        if sheet.cell(row,6).value in (None,""):
                                            created_product_tmpl = product_tmpl_obj.create(vals)
                                            counter = counter + 1  
                                        else:
                                            search_product_tmpl_bar = product_tmpl_obj.search([('barcode','=',sheet.cell(row,6).value)],limit = 1)
                                            if search_product_tmpl_bar:
                                                skipped_line_no[str(counter)] = " - Barcode already exist. "
                                                counter = counter + 1
                                                continue                                            
                                            else:
                                                created_product_tmpl = product_tmpl_obj.create(vals)
                                                counter = counter + 1                                                                           
                                  
                                if created_product_tmpl and created_product_tmpl.product_variant_id and created_product_tmpl.type == 'product' and sheet.cell(row,17).value != '':
                                    stock_vals = {'product_tmpl_id' : created_product_tmpl.id,
                                                  'new_quantity'    : sheet.cell(row,17).value, 
                                                  'product_id'      : created_product_tmpl.product_variant_id.id
                                                  }
                                    created_qty_on_hand = self.env['stock.change.product.qty'].create(stock_vals)
                                    if created_qty_on_hand:
                                        created_qty_on_hand.change_product_qty()                                    
                                    
                                    
                            else:
                                skipped_line_no[str(counter)]=" - Name is empty. "  
                                counter = counter + 1      
                        except Exception as e:
                            skipped_line_no[str(counter)]=" - Value is not valid. " + ustr(e)   
                            counter = counter + 1 
                            continue          
                            
                except Exception:
                    raise UserError(_("Sorry, Your excel file does not match with our format"))
                
                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(completed_records, skipped_line_no)
                    return res
                            
