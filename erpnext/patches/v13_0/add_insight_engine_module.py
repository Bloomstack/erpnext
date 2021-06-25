import frappe

def execute():
	if not frappe.db.exists("Module Def", "Insight Engine"):
		frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Insight Engine",
			"app_name": "erpnext"
		}).insert(ignore_permissions=True)