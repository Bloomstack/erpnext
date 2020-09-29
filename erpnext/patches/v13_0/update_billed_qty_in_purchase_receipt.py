import frappe


def execute():
	frappe.reload_doc("buying", "doctype", "buying_settings")
	frappe.reload_doc("stock", "doctype", "purchase_receipt_item")
	frappe.reload_doc("stock", "doctype", "purchase_receipt")

	buying_settings = frappe.get_single("Buying Settings")
	buying_settings.check_overbilling_against = "Amount"
	buying_settings.save()

	purchase_invoices = frappe.get_all("Purchase Invoice", filters={"docstatus": 1})
	for invoice in purchase_invoices:
		invoice_doc = frappe.get_doc("Purchase Invoice", invoice.name)
		invoice_doc.update_billing_status_in_pr(update_modified=False)
