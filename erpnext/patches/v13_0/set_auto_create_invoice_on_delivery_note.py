import frappe

def execute():
	frappe.reload_doc("accounts", "doctype", "accounts_settings")

	if frappe.get_meta("Accounts Settings").has_field("auto_create_invoice_on_delivery_note_submit"):
		create_invoice_on_submit = frappe.db.get_single_value("Accounts Settings", "auto_create_invoice_on_delivery_note_submit")
		if create_invoice_on_submit:
			frappe.db.set_value("Accounts Settings", None, "auto_create_invoice_on_delivery_note", "Submit")

	frappe.delete_doc_if_exists("Custom Field", "Accounts Settings-auto_create_invoice_on_delivery_note_submit")
