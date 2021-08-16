# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, cint

def execute(filters=None):
	columns = ['Day', 'Ideal', 'Actual']
	project = frappe.get_doc('Project', filters.get("project"))
	total_effort = frappe.db.sql("""select sum(task.task_weight) from `tabTask` task, `tabTask Project` task_project 
		where task.name=task_project.parent and task_project.project=%s""", project.name)[0][0]

	holidays = []
	sprint_days={}
	if project.holiday_list:
		for row in frappe.get_doc("Holiday List", project.holiday_list).holidays:
			holidays.append(row.holiday_date)
	
	actual_effort = {}
	querry = """select task_project.completion_date completion_date, 
		sum(task_weight) total_effort from `tabTask` task, `tabTask Project` task_project 
		where task.name=task_project.parent and task_project.project=%s 
		group by completion_date order by completion_date"""
	
	for day in frappe.db.sql(querry, project.name, as_dict=1):
		actual_effort[day.completion_date] = day.total_effort

	pending_effort = total_effort
	date = project.expected_start_date
	while date <= project.expected_end_date:
		pending_effort = cint(pending_effort - actual_effort.get(date, 0))
		if date not in holidays:
			sprint_days[date] = pending_effort
		date = add_days(date, 1)

	ideal_burn_rate = frappe.utils.safe_div(total_effort, len(sprint_days))

	day = 1
	data = [['Day 0', total_effort, total_effort]]
	for date in sprint_days:
		total_effort -= ideal_burn_rate
		data.append(["Day " + str(day), cint(total_effort), sprint_days.get(date)])
		day += 1
	return columns, data

