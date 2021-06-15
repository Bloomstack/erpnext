# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, nowdate, add_days, now
from frappe.utils.jinja import render_template
from erpnext import get_default_company
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from frappe.model.mapper import get_mapped_doc
from frappe.utils.jinja import render_template


class Contract(Document):
	def autoname(self):
		if self.party_type == "Employee":
			name = self.employee_name
		else:
			name = self.party_name

		if self.contract_template:
			name += " - {} Agreement".format(self.contract_template)

		# If identical, append contract name with the next number in the iteration
		if frappe.db.exists("Contract", name):
			count = len(frappe.get_all("Contract", filters={"name": ["like", "%{}%".format(name)]}))
			name = "{} - {}".format(name, count)

		self.name = _(name)

	def validate(self):
		self.validate_dates()
		self.update_contract_status()
		self.update_fulfilment_status()
		self.generate_contract_terms_display()

	def before_submit(self):
		self.signed_by_company = frappe.session.user

	def on_update_after_submit(self):
		self.create_project_against_contract()
		self.create_order_against_contract()

	def before_submit(self):
		self.set_contract_company()

	def on_submit(self):
		self.create_event_against_contract()

	def before_update_after_submit(self):
		self.update_contract_status()
		self.update_fulfilment_status()
	
	def on_cancel(self):
		self.cancel_event_against_contract()

	def validate_dates(self):
		if self.end_date and self.end_date < self.start_date:
			frappe.throw(_("End Date cannot be before Start Date."))

	def update_contract_status(self):
		if self.is_signed:
			self.status = get_status(self.start_date, self.end_date)
		else:
			self.status = "Unsigned"

	def update_fulfilment_status(self):
		fulfilment_status = "N/A"

		if self.requires_fulfilment:
			fulfilment_progress = self.get_fulfilment_progress()

			if not fulfilment_progress:
				fulfilment_status = "Unfulfilled"
			elif fulfilment_progress < len(self.fulfilment_terms):
				fulfilment_status = "Partially Fulfilled"
			elif fulfilment_progress == len(self.fulfilment_terms):
				fulfilment_status = "Fulfilled"

			if fulfilment_status != "Fulfilled" and self.fulfilment_deadline:
				now_date = getdate(nowdate())
				deadline_date = getdate(self.fulfilment_deadline)

				if now_date > deadline_date:
					fulfilment_status = "Lapsed"

		self.fulfilment_status = fulfilment_status

	def get_fulfilment_progress(self):
		return len([term for term in self.fulfilment_terms if term.fulfilled])

	def generate_contract_terms_display(self):
		if self.contract_terms:
			self.contract_terms_display = render_template(self.contract_terms, {"doc": self.as_dict()})
	
	def create_project_against_contract(self):
		if self.project:
			return

		if not self.project_template:
			return

		if not self.is_signed:
			return

		# Get the tasks for the project
		base_date = getdate(now())
		project_template = frappe.get_doc("Project Template", self.project_template)

		# Get project and party details
		project_name = "{} - {}".format(self.party_name, project_template.template_name)
		if frappe.db.exists("Project", project_name):
			count = len(frappe.get_all("Project", filters={"name": ["like", "%{}%".format(project_name)]}))
			project_name = "{} - {}".format(project_name, count)

		project = frappe.new_doc("Project")
		project.update({
			"project_name": project_name,
			"customer": self.party_name if self.party_type == "Customer" else None,
		})

		project.insert(ignore_permissions=True)

		project_dates = []
		project_name = project.name
		for task in project_template.tasks:
			project_task = frappe.new_doc("Task")
			start_date = add_days(base_date, task.days_to_task_start)
			end_date = add_days(base_date, task.days_to_task_end)
			project_task.update({
				"subject": task.task_name,
				"start_date": start_date,
				"end_date": end_date,
				"task_weight": task.weight,
				"description": task.description,
				"project": project_name
			})
			project_task.insert(ignore_permissions=True)
			project_dates.extend([start_date, end_date])

		expected_start_date = min(project_dates)
		expected_end_date = max(project_dates)

		project.update({
			"expected_start_date": expected_start_date,
			"expected_end_date": expected_end_date
		})

		project.save(ignore_permissions=True)


		# Link the contract with the project
		self.db_set("project", project.name)

	def create_order_against_contract(self):
		if frappe.db.exists("Sales Order", {"contract": self.name}):
			return

		if not self.is_signed:
			return

		if self.document_type == "Quotation" and self.document_name:
			sales_order = make_sales_order(self.document_name)
			sales_order.contract = self.name
			sales_order.project = self.project
			sales_order.delivery_date = frappe.db.get_value("Project", self.project, "expected_end_date")
			sales_order.save()
			sales_order.submit()

	def set_contract_company(self):
		self.signed_by_company = frappe.session.user
		if self.company:
			self.letter_head = frappe.db.get_value("Company", self.company, "default_letter_head")

	def create_event_against_contract(self):
		if not self.end_date:
			return

		employee_id = frappe.db.get_value('Employee', {'user_id': self.signed_by_company}, 'name')
		event = frappe.new_doc('Event')
		event.subject = self.name
		event.ends_on = self.end_date
		event.description = self.contract_terms
		event.all_day = 1
		event.append("event_participants", {
			"reference_doctype": self.party_type,
			"reference_docname": self.party_name
		})

		if employee_id:
			event.append("event_participants", {
				"reference_doctype": 'Employee',
				"reference_docname": employee_id
			})

		event.save()
	
	def cancel_event_against_contract(contract, method):
		event_name = frappe.db.exists('Event', {'subject': contract.name})
		if event_name:
			frappe.delete_doc('Event', event_name)

def get_status(start_date, end_date):
	"""
	Get a Contract's status based on the start, current and end dates

	Args:
		start_date (str): The start date of the contract
		end_date (str): The end date of the contract

	Returns:
		str: 'Active' if within range, otherwise 'Inactive'
	"""

	if not end_date:
		return "Active"

	start_date = getdate(start_date)
	end_date = getdate(end_date)
	now_date = getdate(nowdate())

	return "Active" if start_date <= now_date <= end_date else "Inactive"


def update_status_for_contracts():
	"""
	Run the daily hook to update the statuses for all signed
	and submitted Contracts
	"""

	contracts = frappe.get_all("Contract",
								filters={"is_signed": True,
										"docstatus": 1},
								fields=["name", "start_date", "end_date"])

	for contract in contracts:
		status = get_status(contract.get("start_date"),
							contract.get("end_date"))

		frappe.db.set_value("Contract", contract.get("name"), "status", status)


@frappe.whitelist()
def get_party_users(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("party_type") in ("Customer", "Supplier"):
		party_links = frappe.get_all("Dynamic Link",
			filters={"parenttype": "Contact",
				"link_doctype": filters.get("party_type"),
				"link_name": filters.get("party_name")},
			fields=["parent"])

		party_users = [frappe.db.get_value("Contact", link.parent, "user") for link in party_links]

		return frappe.get_all("User", filters={"email": ["in", party_users]}, as_list=True)
	return []


@frappe.whitelist()
def get_events(start, end, filters=None):
	"""
	Returns events for Gantt / Calendar view rendering.

	Args:
		start (str): Start date-time.
		end (str): End date-time.
		filters (str, optional): Filters (JSON). Defaults to None.

	Returns:
		list of dict: The list of Contract events
	"""

	filters = json.loads(filters)
	from frappe.desk.calendar import get_event_conditions
	conditions = get_event_conditions("Contract", filters)

	events = frappe.db.sql("""
		SELECT
			name,
			start_date,
			end_date
		FROM
			`tabContract`
		WHERE
			(start_date <= %(end)s
				AND end_date >= %(start)s)
				AND docstatus < 2
				{conditions}
		""".format(conditions=conditions), {
			"start": start,
			"end": end
		},
		as_dict=True,
		update={"allDay": 0}
	)
	return events
