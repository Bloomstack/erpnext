import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields    

from erpnext.erpnext_integrations.doctype.taxjar_configuration.taxjar_configuration import add_permissions

def execute():
	enabled = frappe.get_all("TaxJar Configuration", filters={"enabled": True})

	if not enabled:
		return
	
	custom_fields = {
		'Quotation Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
		],
		'Sales Order Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
		],
		'Sales Invoice Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
		],
		'Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='item_group', options='Product Tax Categories',
				label='Product Tax Code')
		]
	}
	create_custom_fields(custom_fields, update=True)
	add_permissions()
	for name in enabled:
		taxjar_configuration = frappe.get_doc("TaxJar Configuration", name)
		taxjar_configuration.sync_product_tax_code()
		break
