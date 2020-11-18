import frappe

def execute():
	priorities = [
		{'doctype': 'Issue Priority', 'name': 'Low'},
		{'doctype': 'Issue Priority', 'name': 'Medium'},
		{'doctype': 'Issue Priority', 'name': 'High'}
	]

	for priority in priorities:
		if not frappe.db.exists('Issue Priority', priority.get('name')):
			frappe.get_doc(priority).insert(ignore_permissions=True)
