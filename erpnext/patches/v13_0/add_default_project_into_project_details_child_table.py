from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task_project')
	frappe.reload_doc('projects', 'doctype', 'task')
	frappe.reload_doc('projects', 'doctype', 'project')

	tasks = frappe.db.get_all("Task", fields=["name", "default_project", "status"])
	for task in tasks:
		if task.default_project:
			doc = frappe.get_doc("Task", task.name)
			if not doc.status:
				doc.status = "Closed"
			doc.append("projects", {
				"project": task.default_project,
				"status": task.status,
				"is_default": 1
			})
			doc.flags.ignore_validate=True
			doc.save()
