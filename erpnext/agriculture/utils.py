import frappe
from frappe.utils import add_days

def create_project(project_name, start_date, period):
	project = frappe.get_doc({
		"doctype": "Project",
		"project_name": project_name,
		"expected_start_date": start_date,
		"expected_end_date": add_days(start_date, period - 1)
	}).insert()
	return project.name

def create_tasks(tasks, project_name, start_date):
	for task in tasks:
		frappe.get_doc({
			"doctype": "Task",
			"subject": task.get("task_name"),
			"priority": task.get("priority"),
			"default_project": project_name
		}).insert()
