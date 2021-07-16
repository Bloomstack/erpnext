# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import cint, getdate, formatdate, today, add_days, get_date_str, add_to_date
from frappe import throw, _
from frappe.model.document import Document

class OverlapError(frappe.ValidationError): pass

class HolidayList(Document):
	def validate(self):
		self.validate_days()
		self.total_holidays = len(self.holidays)

	def get_weekly_off_dates(self):
		self.validate_values()
		date_list = self.get_weekly_off_date_list(self.from_date, self.to_date)
		last_idx = max([cint(d.idx) for d in self.get("holidays")] or [0,])
		for i, d in enumerate(date_list):
			ch = self.append('holidays', {})
			ch.description = self.weekly_off
			ch.holiday_date = d
			ch.idx = last_idx + i + 1
			ch.is_weekly_off = 1

	def validate_values(self):
		if not self.weekly_off:
			throw(_("Please select weekly off day"))


	def validate_days(self):
		if self.from_date > self.to_date:
			throw(_("To Date cannot be before From Date"))

		for day in self.get("holidays"):
			if not (getdate(self.from_date) <= getdate(day.holiday_date) <= getdate(self.to_date)):
				frappe.throw(_("The holiday on {0} is not between From Date and To Date").format(formatdate(day.holiday_date)))

	def get_weekly_off_date_list(self, start_date, end_date):
		start_date, end_date = getdate(start_date), getdate(end_date)

		from dateutil import relativedelta
		from datetime import timedelta
		import calendar

		date_list = []
		existing_date_list = []
		weekday = getattr(calendar, (self.weekly_off).upper())
		reference_date = start_date + relativedelta.relativedelta(weekday=weekday)

		existing_date_list = [getdate(holiday.holiday_date) for holiday in self.get("holidays")]

		while reference_date <= end_date:
			if reference_date not in existing_date_list:
				date_list.append(reference_date)
			reference_date += timedelta(days=7)

		return date_list

	def clear_table(self):
		self.set('holidays', [])

@frappe.whitelist()
def create_events(holiday_list):
	def create_holiday_event(holiday, holiday_list):
		frappe.get_doc({
			"doctype": "Event",
			"subject": "Holiday " + add_to_date(holiday.holiday_date, as_string=True),
			"starts_on": holiday.holiday_date,
			"event_category": "Holiday",
			"holiday_list": holiday_list,
			"event_type": "Public",
			"all_day":1
		}).insert(ignore_permissions=True)

	doc = frappe.get_doc("Holiday List", holiday_list)
	calendar_events = frappe.get_all("Event", filters={"holiday_list": doc.name}, fields=["name", "starts_on"])
	if not calendar_events:
		for holiday in doc.holidays:
			if holiday.is_weekly_off:
				continue

			create_holiday_event(holiday, doc.name)
	else:
		holidays = [frappe.utils.get_datetime_str(holiday.holiday_date) for holiday in doc.holidays if not holiday.is_weekly_off]
		starts_on = []

		for event in calendar_events:
			starts_on.append(frappe.utils.get_datetime_str(event.starts_on))
			if not frappe.utils.get_datetime_str(event.starts_on) in holidays:
				frappe.delete_doc("Event", event.name)

		for holiday in doc.holidays:
			if holiday.is_weekly_off or frappe.utils.get_datetime_str(holiday.holiday_date) in starts_on:
				continue

			create_holiday_event(holiday, doc.name)

	return True

@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Gantt / Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	if filters:
		filters = json.loads(filters)
	else:
		filters = []

	if start:
		filters.append(['Holiday', 'holiday_date', '>', getdate(start)])
	if end:
		filters.append(['Holiday', 'holiday_date', '<', getdate(end)])

	return frappe.get_list('Holiday List',
		fields=['name', '`tabHoliday`.holiday_date', '`tabHoliday`.description', '`tabHoliday List`.color'],
		filters = filters,
		update={"allDay": 1})


def is_holiday(holiday_list, date=today()):
	"""Returns true if the given date is a holiday in the given holiday list
	"""
	if holiday_list:
		return bool(frappe.get_all('Holiday List',dict(name=holiday_list, holiday_date=date)))
	else:
		return False

def send_holiday_notification():
	"""Sends an email for list of holidays falling in 7 days from today
	"""
	# holidays is a list of holidays which fall in 7 days from today
	today_date = today()
	holiday_lists = frappe.get_all('Holiday List', filters={"enabled" : 1}, fields=["name", "send_reminders_to", "notification_message"])

	for holiday_list in holiday_lists:
		end_date = get_date_str(add_days(today(), 7))
		holidays = frappe.get_all('Holiday', filters={"parent": holiday_list.name, "holiday_date": ["BETWEEN", [today_date, end_date]]}, fields=["holiday_date", "description"])

		if holidays:
			# Forming a new String to make a table with all the Holidays
			_holiday = ""
			for holiday in holidays:
				_holiday += """
					<tr>
						<td>{0}</td>
						<td>{1}</td>
						<td>{2}</td>
					</tr>
				""".format(formatdate(holiday.holiday_date), frappe.utils.get_weekday(holiday.holiday_date), holiday.description)

			holiday_table = """
				<table>
					<thead>
						<tr>
							<th>Date</th>
							<th>Day</th>
							<th>Description</th>
						</tr>
					</thead>
					<tbody>
						{0}
					</tbody>
				</table>
			""".format(_holiday)

			recipients = [d.email for d in frappe.get_all("Email Group Member",filters={"email_group": holiday_list.send_reminders_to}, fields=["email"])]
			message = holiday_list.notification_message + '<br>' + holiday_table
			frappe.sendmail(
				recipients=recipients,
				subject="Holiday Notification",
				message=message
			)
