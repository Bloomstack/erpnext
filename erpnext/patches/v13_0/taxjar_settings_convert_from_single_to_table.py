import frappe
from frappe.utils.password import get_decrypted_password

def execute():
	# Why converting taxjar settings into table. Because taxjar does not support multi company
	# for multi company taxjar contains multiple taxjar account with api keys.
	frappe.reload_doc("ERPNext Integrations", "doctype", "TaxJar Configuration", force=1)
	frappe.reload_doc("ERPNext Integrations", "doctype", "TaxJar Nexus", force=1)
	if frappe.db.exists("TaxJar Settings"):
		# Since taxjar settings doctype deleted. for existing site we can fetch data from database.
		taxjar_settings = frappe.db.get_singles_dict("TaxJar Settings")
		if taxjar_settings and taxjar_settings.tax_account_head:
			company = frappe.db.get_value('Account', taxjar_settings.tax_account_head, "company")

			new_taxjar_settings = frappe.new_doc("TaxJar Configuration")
			new_taxjar_settings.enabled = taxjar_settings.enabled
			new_taxjar_settings.company = company
			new_taxjar_settings.is_sandbox = taxjar_settings.is_sandbox
			new_taxjar_settings.taxjar_calculate_tax = taxjar_settings.taxjar_calculate_tax
			new_taxjar_settings.taxjar_create_transactions = taxjar_settings.taxjar_create_transactions
			new_taxjar_settings.api_key = get_decrypted_password("TaxJar Settings", "TaxJar Settings", fieldname='api_key')
			new_taxjar_settings.sandbox_api_key = get_decrypted_password("TaxJar Settings", "TaxJar Settings", fieldname='sandbox_api_key')
			new_taxjar_settings.tax_account_head = taxjar_settings.tax_account_head
			new_taxjar_settings.shipping_account_head = taxjar_settings.shipping_account_head
			new_taxjar_settings.save()

		# once data added to taxjar configuration delete taxjar settings from database too.
		frappe.delete_doc_if_exists("DocType", "TaxJar Settings")
	frappe.delete_doc_if_exists("DocType", "Taxjar Company")
