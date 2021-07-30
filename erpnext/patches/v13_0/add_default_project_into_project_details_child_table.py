from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task')
	frappe.reload_doc('projects', 'doctype', 'task_project')

	tasks = frappe.db.get_all("Task", fields=["*"])
	for task in tasks:
		if task.project:
			doc = frappe.get_doc("Task", task.name)
			doc.append("projects", {
				"project": task.project,
				"status": task.status
			})
			doc.save()