import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields    

def execute():
	enabled = frappe.get_all("TaxJar Configuration", filters={"enabled": True})

	if not enabled:
		return
	
	custom_fields = {
		'Quotation Item': [
			dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		],
		'Sales Order Item': [
			dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		],
		'Sales Invoice Item': [
            dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		]
	}
	create_custom_fields(custom_fields, update=True)
