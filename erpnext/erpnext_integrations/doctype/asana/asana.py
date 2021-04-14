# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import asana
from datetime import datetime
from frappe.model.document import Document
from frappe import _
from frappe.utils.password import get_decrypted_password

class Asana(Document):
	def validate(self):
		self.authorize()


	def authorize(self):
		"""Authenticate the token and return asana client"""
		if self.enable and not self.personal_access_token:
			frappe.throw(_("Personal Access Token is mandatory if Asana Integration is enabled."))
		try:
			client = asana.Client.access_token(get_decrypted_password("Asana", "Asana", "personal_access_token"))
			return client
		except Exception as e:
			frappe.throw(_("Error while connecting to Asana Client."))


	def send_email_reminder(self):
		"""
		Sends an email reminder to the assignee of the asana task if no comments have been added to it for more than
		the number of days specified in the number_of_stale_days.
		"""

		if not self.enable:
			return

		client = self.authorize()
		asana_workspaces = client.workspaces.get_workspaces()
		workspaces = self.workspaces.split(",")

		for workspace in workspaces:
			workspace = workspace.strip()
			asana_workspace = next((item for item in asana_workspaces if item["name"] == workspace), None)
			if not workspace:
				frappe.msgprint(_("Workspace {0} not found in Asana.".format(asana_workspace)))

			projects = self.projects.split(",")
			asana_projects = client.projects.find_all({"workspace": asana_workspace["gid"]})
			for project in projects:
				project = project.strip()
				asana_project = next((item for item in asana_projects if item["name"] == project), None)
				if not asana_project:
					frappe.msgprint(_("Project {0} not found in Asana.".format(asana_project)))

				sections = self.sections.split(",")
				asana_sections = client.sections.get_sections_for_project(asana_project["gid"])
				for section in sections:
					section = section.strip()
					asana_section = next((item for item in asana_sections if item["name"] == section), None)
					if not asana_section:
						frappe.msgprint(_("Section {0} not found in Asana.".format(asana_section)))

					tasks = client.tasks.find_all({"section": asana_section["gid"]})
					for task in list(tasks):
						asana_task = client.tasks.get_task(task["gid"])
						stories = list(client.stories.get_stories_for_task(asana_task["gid"]))
						assignee_email = client.users.get_user(asana_task["assignee"]["gid"])["email"]
						comment_added = False
						for i in range(len(stories)-1, 0, -1):
							if stories[i]["resource_subtype"] == "comment_added":
								comment_added = True
								asana_task_last_updated = stories[i]["created_at"].split("T")[0]
								now_date = datetime.utcnow().strftime("%Y-%m-%d")
								if ((datetime.strptime(asana_task_last_updated, "%Y-%m-%d") -
										datetime.strptime(now_date, "%Y-%m-%d")).days <= -self.number_of_stale_days):
									frappe.sendmail(recipients=[assignee_email], message="task {0} is not updated in the last {1} days!!".format(asana_task["name"], self.number_of_stale_days))
								break
						if not comment_added:
							frappe.sendmail(recipients=[assignee_email], message="No comment added for task {0}!!".format(asana_task["name"]))


def daily_asana_email_notification():
	"""Daily scheduler to send asana email notifications"""
	asana_doc = frappe.get_single("Asana")
	asana_doc.send_email_reminder()