# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
import random
from frappe.utils import comma_and, cint
from frappe.desk.form.utils import add_comment
from frappe.utils.background_jobs import enqueue
from frappe.model.document import Document

class AsanaMigrator(Document):
	def validate(self):
		if self.docstatus == 1:
			self.validate_tasks()

	def validate_tasks(self):
		tasks = json.loads(self.row_data) if self.row_data else []

		if len(tasks) == 0:
			frappe.throw(_('No Tasks found please, click on "Get Task" or check the respective Project on your Asana Instance.'))	

	def get_tasks(self):
		if self.selected_project and self.selected_workspace:
			data = []
			client = authorize()
			project_global_id = self.selected_project.split(" - ")[1]

			frappe.publish_realtime('fetching_task', dict(progress = 2))
			#converting Generator Objrct in List
			tasks = [task for task in client.tasks.find_all({"project": project_global_id})]
			task_comments = {}
			count = 1
			for task in tasks:
				task = frappe._dict(task)
				task_details = self.get_task_details(task.gid, client)
				task_row = self.get_row_data(task_details)
				comments = self.get_comments(task_details.gid, client)
				if len(comments):
					task_comments[str(task.gid)] = comments
				data.append(task_row)
				count += 1
				frappe.publish_realtime('fetching_task', dict(progress = count*100/len(tasks)))
				# frappe.publish_progress, title = _("Fetching Tasks and Comments..."))

		if not len(data):
			frappe.throw(_("No Tasks found for Project: {0}").format(self.selected_project))
		self.row_data = json.dumps(data)
		self.tasks_comment = json.dumps(task_comments)
		self.save()
	
	def import_tasks(self, tasks_to_import, comments_to_import):

		self.db_set("status","In Progress")		

		if len(tasks_to_import) > 10:
			frappe.enqueue(create_tasks, timeout=600,
				tasks_to_import=tasks_to_import, comments_to_import=comments_to_import,
					project=self.selected_project, skip_completed_tasks=self.skip_completed_tasks)
		else:
			create_tasks(tasks_to_import, comments_to_import, self.selected_project, self.skip_completed_tasks)

		self.db_set("status", "Completed")

	def get_task_details(self, global_id, client):
			return frappe._dict(client.tasks.get_task(global_id))

	def get_row_data(self, task_details):
		assigned_user = []

		if task_details.assignee:
			assigned_user = [value for key, value in task_details.assignee.items() if key == "name"]

		parent_id = ''
		parent_name = ''
		if task_details.parent:
			parent = frappe._dict(task_details.parent)
			parent_id = parent.gid
			parent_name = parent.name

		return {
			"name": task_details.name,
			"global_id": task_details.gid,
			"notes": task_details.notes or '',
			"assignee": comma_and(assigned_user) if len(assigned_user) else '',
			"status": "Completed" if task_details.completed else "In Progress",
			"completed_on": task_details.created_at,
			"parent_id":  parent_id,
			"parent_name": parent_name,
			"reference": task_details.permalink_url
		}

	def get_comments(self, task_gid, client):
		#converting Generator Odject intp list of dict
		comments = []
		for comment in client.stories.get_stories_for_task(task_gid):
			if comment.get('resource_subtype', None) == "comment_added":
				comments.append(comment)

		return comments


def create_tasks(tasks_to_import, comments_to_import, project, skip_completed_tasks):
	#Sorted for creating parent tasks first.
	task_dict = sorted(tasks_to_import, key = lambda i: i['parent_id'], reverse = False)
	project = create_project(project)
	
	for data in task_dict:
		data = frappe._dict(data)
		if frappe.db.exists("Task", {"subject": data.name}): 
			continue

		if data.status == "Completed" and skip_completed_tasks:
			continue

		task = frappe.new_doc("Task")
		task.subject = data.name
		task.description = data.notes
		task.status = data.status if data.status == "Completed" else "Open"
		task.append("projects", {'project': project})
		parent = frappe.db.exists("Task", {"subject": data.parent_name})
		if parent:
			task.parent_task = parent
			frappe.db.set_value("Task", parent ,"is_group", 1)
		try: 
			task.save()
		except Exception as e:
			frappe.log_error(e)

		_add_comments(task.name, comments_to_import, data.global_id, data.assignee, data.reference)
		
def _add_comments(task, comments_to_import, global_id, assignee, reference):
	comment_text = ''
	task_detail_text = ''
	task_comments = comments_to_import.get(global_id)
	if task_comments:
		for comment in task_comments:
			comment_text += " " + "<b>" +comment["created_by"]["name"]+ ": </b>"
			comment_text += comment["text"]
			comment_text += "<br><br>"
	if assignee:
		task_detail_text = _("This Task was assigned to {0}").format(assignee)
	task_detail_text +=  "<br>" + "Reference: " 
	task_detail_text += "<a href="+(reference)+">" + (reference)+ "</a>"
	for comment in [comment_text, task_detail_text]:
		try:
			add_comment("Task", task, comment, frappe.session.user, frappe.session.user_fullname)
		except Exception as e:
			frappe.log_error(e)

def create_project(asana_project):
	project_global_id = asana_project.split(" - ")[1]

	client = authorize()
	project_details = client.projects.get_project(project_global_id)
	project_details = frappe._dict(project_details)

	if frappe.db.exists("Project", project_details.name):
		return project_details.name

	project = frappe.new_doc("Project")
	project.project_name = project_details.name
	project.notes = project_details.notes
	project.save()

	return project.name

@frappe.whitelist()
def get_workspaces():
	asana_settings = frappe.get_single("Asana Settings")
	asana_workspaces = asana_settings.get_workspaces()
	worksapces = []
	for workspace in asana_workspaces:
		worksapces.append(workspace)

	if len(worksapces):
		return worksapces
	else:
		frappe.throw(_("No Workspace found on Asana"))

@frappe.whitelist()
def get_projects(global_id):
	client = authorize()
	asana_projects = client.projects.find_all({"workspace": global_id})
	projects = []
	for project in asana_projects:
		projects.append(project)

	if len(projects):
		return projects
	else:
		frappe.throw(_("No Projects found for Workspace"))

def authorize():
	return frappe.get_single("Asana Settings").authorize()

