import frappe, json

def execute():
	from erpnext.setup.setup_wizard.operations.install_fixtures import add_status_data, add_status_workflow_data

	frappe.reload_doc("setup", "doctype", "Status")
	frappe.reload_doc("setup", "doctype", "Status Workflow")

	add_status_data()
	add_status_workflow_data()