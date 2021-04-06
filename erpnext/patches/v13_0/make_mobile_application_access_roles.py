import frappe


def execute():
	roles = [
		{
			"role_name": "Expense Module",
			"for_mobile_application": 1
		},
		{
			"role_name": "Driver Module",
			"for_mobile_application": 1
		}
	]
	for role in roles:
		frappe.get_doc({
			"doctype": "Role",
			"role_name": role.get("role_name"),
			"for_mobile_application": role.get("for_mobile_application")
		}).insert(ignore_permissions=True)