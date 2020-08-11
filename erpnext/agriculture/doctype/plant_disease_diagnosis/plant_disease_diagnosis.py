# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.agriculture.utils import create_project, create_tasks

class PlantDiseaseDiagnosis(Document):
	def validate(self):
		max_period = 0
		for task in self.treatment_task:
			# validate start_day is not > end_day
			if task.start_day > task.end_day:
				frappe.throw(_("Start day is greater than end day in task '{0}'").format(task.task_name))
			# to calculate the period of the Crop Cycle
			if task.end_day > max_period: max_period = task.end_day
		self.treatment_period = max_period

	def before_submit(self):
		self.create_tasks_for_diseases()

	def create_tasks_for_diseases(self):
		project_name = self.disease + "-" + self.plant_batch
		if self.plant:
			project_name = self.disease + "-" + self.plant

		if frappe.db.exists("Project", project_name):
			project_name = project_name + "-" + self.diagnosis_date

		self.project = create_project(project_name, self.treatment_start_date, self.treatment_period)
		create_tasks(self.treatment_task, self.project, self.treatment_start_date)

	def get_treatment_tasks(self):
		return frappe.get_all('Cultivation Task', fields=["task_name", "holiday_management", "start_day", "end_day", "priority"],
			filters={'parenttype': 'Disease', 'parent': self.disease}, order_by="idx")
