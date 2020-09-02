import frappe

def execute():
	# delete old Agri Doctypes
	for doctype in ['Fertilizer', 'Fertilizer Content', 'Crop', 'Crop Cycle', 'Agriculture Task']:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype)