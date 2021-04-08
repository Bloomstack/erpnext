import frappe

def execute():
	custom_fields = ["column_break_59", "section_break_56", "licenses_sb", "licenses"]

	for field in custom_fields:
		frappe.delete_doc_if_exists("Custom Field", field)