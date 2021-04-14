import frappe


def execute():
	frappe.reload_doc("core", "doctype", "role", force=1)
	roles = ["Expense Module", "Driver Module"]
	for role in roles:
		if frappe.db.exists("Role", role):
			frappe.db.set_value("Role", role, "for_mobile_application", 1)
		else:
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"for_mobile_application": 1,
			}).insert(ignore_permissions=True)
