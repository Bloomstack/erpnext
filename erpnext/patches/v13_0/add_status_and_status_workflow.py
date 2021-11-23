import frappe, json

def execute():
	from erpnext.setup.setup_wizard.operations.install_fixtures import add_status_data, add_status_workflow_data

	frappe.reload_doc("core", "doctype", "Status", force=True)
	frappe.reload_doc("core", "doctype", "Status Workflow", force=True)

	add_status_data()
	add_status_workflow_data()