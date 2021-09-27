import frappe

def execute():
	# Why converting taxjar settings into table. Because taxjar does not support multi company
	# for multi company taxjar contains multiple taxjar account with api keys. 
	frappe.reload_doc("ERPNext Integrations", "doctype", "TaxJar Settings", force=1)
	taxjar_settings = frappe.get_single("TaxJar Settings")
	if taxjar_settings and taxjar_settings.tax_account_head:
		company = frappe.db.get_value('Account', taxjar_settings.tax_account_head, "company")

		new_taxjar_settings = frappe.new_doc("TaxJar Settings")
		new_taxjar_settings.enabled = taxjar_settings.enabled
		new_taxjar_settings.company = company
		new_taxjar_settings.is_sandbox = taxjar_settings.is_sandbox
		new_taxjar_settings.taxjar_calculate_tax = taxjar_settings.taxjar_calculate_tax
		new_taxjar_settings.taxjar_create_transactions = taxjar_settings.taxjar_create_transactions
		new_taxjar_settings.api_key = taxjar_settings.get_password("api_key")
		new_taxjar_settings.sandbox_api_key = taxjar_settings.get_password("sandbox_api_key")
		new_taxjar_settings.tax_account_head = taxjar_settings.tax_account_head
		new_taxjar_settings.shipping_account_head = taxjar_settings.shipping_account_head
		new_taxjar_settings.save()
	
		taxjar_settings.delete()

	