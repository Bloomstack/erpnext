from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task_project')
	frappe.reload_doc('projects', 'doctype', 'task')

	tasks = frappe.db.get_all("Task", fields=["name", "project", "status"])
	for task in tasks:
		if task.project:
			doc = frappe.get_doc("Task", task.name)
			if not doc.status:
				doc.status = "Closed"
			doc.append("projects", {
				"project": task.project,
				"status": task.status,
				"is_default": 1
			})
			doc.flags.ignore_validate=True
			doc.save()