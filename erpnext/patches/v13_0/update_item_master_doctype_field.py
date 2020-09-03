import frappe

def execute():
	frappe.reload_doc("stock", "doctype", "item")
	if frappe.db.field_exists('Item', 'inspection_required_before_manufacturing'):
		items = frappe.db.get_all('Item', fields = ['name', 'inspection_required_before_manufacturing'])
		for item in items:
			frappe.db.set_value("Item", item.name, "inspection_required_during_manufacturing", item.inspection_required_before_manufacturing, update_modified=False)