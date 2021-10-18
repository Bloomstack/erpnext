# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import comma_and
from frappe.desk.form.utils import add_comment
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
			project_gid = ''
			client = authorize()
			project_global_id = get_project_gid(self.project_options, self.selected_project)

			frappe.publish_realtime('fetching_task', dict(
				progress = 2, heading="Getting tasks", label = 'Fetching Tasks and comments.'))
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
				frappe.publish_realtime('fetching_task', dict(
					progress = count*100/len(tasks), heading="Getting tasks", label = 'Fetching Tasks and comments.'))

		if not len(data):
			frappe.throw(_("No Tasks found for Project: {0}").format(self.selected_project))
		self.row_data = json.dumps(data)
		self.tasks_comment = json.dumps(task_comments)
		self.save()
	
	def import_tasks(self, tasks_to_import, comments_to_import):
		self.db_set("status","In Progress")

		project_gid = get_project_gid(self.project_options, self.selected_project)

		child_tasks = []
		frappe.publish_realtime('fetching_task', dict(
			progress = 2, heading="Getting  Sub-tasks",
			label = "Looking for Sub-Tasks and Comments"))
		count = 1
		for task in tasks_to_import:
			child_data, child_comment = self.get_child_task(task["global_id"])
			child_tasks += child_data

			while(child_data):
				data, comments = self._get_child_task(child_data)
				child_tasks += data
				child_comment += comments
				child_data = data

			if len(child_comment) and str(task["global_id"]) not in comments_to_import:
				comments_to_import[str(task["global_id"])] = child_comment
			
			count += 1
			frappe.publish_realtime('fetching_task', dict(
				progress = count*100/len(tasks_to_import), heading="Getting  Sub-tasks",
				label = "Looking for Sub-Tasks and Comments"))
		self.save()

		tasks_to_import += child_tasks
		frappe.enqueue(create_tasks, timeout=600,
			tasks_to_import=tasks_to_import, comments_to_import=comments_to_import,
			project_gid=project_gid, skip_completed_tasks=self.skip_completed_tasks)

		self.db_set("status","Completed")

	def _get_child_task(self, childs):
		datas = []
		comments = []
		for child in childs:
			d, c = self.get_child_task(child["global_id"])
			datas += d
			comments += c

		return datas, comments


	def get_child_task(self, gid):
		child_data = []
		child_comment = []
		client = authorize()
		child_tasks = client.tasks.get_subtasks_for_task(gid)
		if child_tasks:
			for task in child_tasks:
				details = self.get_task_details(task['gid'], client)
				child_data.append(self.get_row_data(details))
				comment = self.get_comments(task['gid'], client)
				if len(comment):
					child_comment += comment

		return child_data, child_comment

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


def get_project_gid(project_options, selected_project):
	for details in json.loads(project_options):
		if details['name'] == selected_project:
			return details["gid"]


def create_tasks(tasks_to_import, comments_to_import, project_gid, skip_completed_tasks):
	project = create_project(project_gid)

	for data in tasks_to_import:
		data = frappe._dict(data)
		if frappe.db.exists("Task", {"subject": data.name}): 
			continue

		if data.status == "Completed" and skip_completed_tasks:
			continue

		task = frappe.new_doc("Task")
		task.subject = data.name
		task.description = data.notes
		task.status = data.status if data.status == "Completed" else "Open"
		task.append("projects", {
			'project': project,
			'status': data.status if data.status == "Completed" else "Open",
			'is_default': 1
		})

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
	task_detail_text += "<br>" + "Reference: " 
	task_detail_text += "<a href="+(reference)+">" + (reference)+ "</a>"
	for comment in [comment_text, task_detail_text]:
		try:
			add_comment("Task", task, comment, frappe.session.user, frappe.session.user_fullname)
		except Exception as e:
			frappe.log_error(e)

def create_project(project_global_id):

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

