import frappe

def execute():
	frappe.reload_doc("ERPNext Integrations", "doctype", "TaxJar Company", force=1)
	frappe.reload_doc("ERPNext Integrations", "doctype", "TaxJar Settings", force=1)
	taxjar_settings = frappe.get_doc('TaxJar Settings', None)
	if taxjar_settings.tax_account_head:
		company = frappe.db.get_value('Account', taxjar_settings.tax_account_head,"company")
		taxjar_settings.append("company_account",{
			'tax_account_head': taxjar_settings.tax_account_head,
			'shipping_account_head': taxjar_settings.shipping_account_head,
			'company_name': company
		})
		taxjar_settings.save()
