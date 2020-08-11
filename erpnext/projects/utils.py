# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def query_task(doctype, txt, searchfield, start, page_len, filters):
	from frappe.desk.reportview import build_match_conditions

	search_string = "%%%s%%" % txt
	order_by_string = "%s%%" % txt
	match_conditions = build_match_conditions("Task")
	match_conditions = ("and" + match_conditions) if match_conditions else ""

	return frappe.db.sql("""select name, subject from `tabTask`
		where (`%s` like %s or `subject` like %s) %s
		order by
			case when `subject` like %s then 0 else 1 end,
			case when `%s` like %s then 0 else 1 end,
			`%s`,
			subject
		limit %s, %s""" %
		(searchfield, "%s", "%s", match_conditions, "%s",
			searchfield, "%s", searchfield, "%s", "%s"),
		(search_string, search_string, order_by_string, order_by_string, start, page_len))

@frappe.whitelist()
def update_timesheet_logs(ref_dt, ref_dn, billable):
	time_logs = []

	if ref_dt in ["Project", "Task"]:
		if ref_dt == "Project":
			tasks = update_linked_tasks(ref_dn, billable)
			time_logs = [get_task_time_logs(task) for task in tasks]
			# flatten the list of time log lists
			time_logs = [log for time_log in time_logs for log in time_log]
		else:
			time_logs = frappe.get_all("Timesheet Detail", filters={frappe.scrub(ref_dt): ref_dn})

	elif ref_dt in ["Project Type", "Project Template"]:
		projects = update_linked_projects(frappe.scrub(ref_dt), ref_dn, billable)
		time_logs = [get_project_time_logs(project) for project in projects]
		# flatten the list of time log lists
		time_logs = [log for time_log in time_logs for log in time_log]

	for log in time_logs:
		frappe.db.set_value("Timesheet Detail", log.name, "billable", billable)


def update_linked_projects(ref_field, ref_value, billable):
	projects = frappe.get_all("Project", filters={ref_field: ref_value})

	for project in projects:
		project_doc = frappe.get_doc("Project", project.name)
		project_doc.billable = billable
		project_doc.save()
		update_linked_tasks(project.name, billable)

	return projects


def update_linked_tasks(project, billable):
	tasks = frappe.get_all("Task", filters={"project": project})

	for task in tasks:
		task_doc = frappe.get_doc("Task", task.name)
		task_doc.billable = billable
		task_doc.save()

	return tasks


def get_project_time_logs(project):
	return frappe.get_all("Timesheet Detail", filters={"project": project.name})

def get_task_time_logs(task):
	return frappe.get_all("Timesheet Detail", filters={"task": task.name})

