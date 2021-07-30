from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task')
	frappe.reload_doc('projects', 'doctype', 'project_item')

	tasks = frappe.db.get_all("Task", fields=["*"])
	for task in tasks:
		project_item = frappe.db.get_all("Project Item", filters={"parent":task.name}, fields=["*"])
		if not project_item:
			doc = frappe.get_doc("Task", task.name)
			doc.append("projects", {
				"project": task.project,
				"status": task.status
			})
			doc.save()