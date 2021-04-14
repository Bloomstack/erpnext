# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
from frappe import _
from frappe.utils import get_fullname, flt, cstr
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name
from erpnext.accounts.party import get_party_account
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils.csvutils import getlink
from erpnext.accounts.utils import get_account_currency
from erpnext.hr.doctype.department_approver.department_approver import get_approvers
import json

class InvalidExpenseApproverError(frappe.ValidationError): pass
class ExpenseApproverIdentityError(frappe.ValidationError): pass

class ExpenseClaim(AccountsController):
	def onload(self):
		self.get("__onload").make_payment_via_journal_entry = frappe.db.get_single_value('Accounts Settings',
			'make_payment_via_journal_entry')

	def validate(self):
		self.validate_advances()
		self.validate_sanctioned_amount()
		self.calculate_total_amount()
		set_employee_name(self)
		self.set_expense_account(validate=True)
		self.set_company()
		self.set_payable_account()
		self.set_cost_center()
		self.calculate_taxes()
		self.set_status()
		if self.task and not self.project:
			self.project = frappe.db.get_value("Task", self.task, "project")

	def set_status(self):
		self.status = {
			"0": "Draft",
			"1": "Submitted",
			"2": "Cancelled"
		}[cstr(self.docstatus or 0)]

		paid_amount = flt(self.total_amount_reimbursed) + flt(self.total_advance_amount)
		precision = self.precision("grand_total")
		if (self.is_paid or (flt(self.total_sanctioned_amount) > 0
			and flt(flt(self.total_sanctioned_amount) + flt(self.total_taxes_and_charges), precision) ==  flt(paid_amount, precision))) \
			and self.docstatus == 1 and self.approval_status == 'Approved':
				self.status = "Paid"
		elif flt(self.grand_total) > 0 and self.docstatus == 1 and self.approval_status == 'Approved':
			self.status = "Unpaid"
		elif self.docstatus == 1 and self.approval_status == 'Rejected':
			self.status = 'Rejected'

	def set_company(self):
		if not self.company:
			self.company = frappe.get_value("Employee", self.employee, "company")

	def set_payable_account(self):
		if not self.payable_account and not self.is_paid:
			self.payable_account = frappe.get_cached_value('Company', self.company, 'default_expense_claim_payable_account')

	def set_cost_center(self):
		default_cost_center = frappe.get_cached_value('Company', self.company, 'cost_center')
		if not self.cost_center:
			self.cost_center = default_cost_center
		for expense in self.expenses:
			if not expense.cost_center:
				expense.cost_center = default_cost_center

	def on_submit(self):
		if self.approval_status=="Draft":
			frappe.throw(_("""Approval Status must be 'Approved' or 'Rejected'"""))

		self.update_task_and_project()
		self.make_gl_entries()

		if self.is_paid:
			update_reimbursed_amount(self)

		self.set_status()
		self.update_claimed_amount_in_employee_advance()

	def on_cancel(self):
		self.update_task_and_project()
		if self.payable_account:
			self.make_gl_entries(cancel=True)

		if self.is_paid:
			update_reimbursed_amount(self)

		self.set_status()
		self.update_claimed_amount_in_employee_advance()

	def update_claimed_amount_in_employee_advance(self):
		for d in self.get("advances"):
			frappe.get_doc("Employee Advance", d.employee_advance).update_claimed_amount()

	def update_task_and_project(self):
		if self.task:
			self.update_task()
		elif self.project:
			frappe.get_doc("Project", self.project).update_project()

	def make_gl_entries(self, cancel=False):
		if flt(self.total_sanctioned_amount) > 0:
			gl_entries = self.get_gl_entries()
			make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		self.validate_account_details()

		# payable entry
		if self.grand_total:
			gl_entry.append(
				self.get_gl_dict({
					"account": self.payable_account,
					"credit": self.grand_total,
					"credit_in_account_currency": self.grand_total,
					"against": ",".join([d.default_account for d in self.expenses]),
					"party_type": "Employee",
					"party": self.employee,
					"against_voucher_type": self.doctype,
					"against_voucher": self.name,
					"cost_center": self.cost_center
				}, item=self)
			)

		# expense entries
		for data in self.expenses:
			gl_entry.append(
				self.get_gl_dict({
					"account": data.default_account,
					"debit": data.sanctioned_amount,
					"debit_in_account_currency": data.sanctioned_amount,
					"against": self.employee,
					"cost_center": data.cost_center
				}, item=data)
			)

		for data in self.advances:
			gl_entry.append(
				self.get_gl_dict({
					"account": data.advance_account,
					"credit": data.allocated_amount,
					"credit_in_account_currency": data.allocated_amount,
					"against": ",".join([d.default_account for d in self.expenses]),
					"party_type": "Employee",
					"party": self.employee,
					"against_voucher_type": "Employee Advance",
					"against_voucher": data.employee_advance
				})
			)

		self.add_tax_gl_entries(gl_entry)

		if self.is_paid and self.grand_total:
			# payment entry
			payment_account = get_bank_cash_account(self.mode_of_payment, self.company).get("account")
			gl_entry.append(
				self.get_gl_dict({
					"account": payment_account,
					"credit": self.grand_total,
					"credit_in_account_currency": self.grand_total,
					"against": self.employee
				}, item=self)
			)

			gl_entry.append(
				self.get_gl_dict({
					"account": self.payable_account,
					"party_type": "Employee",
					"party": self.employee,
					"against": payment_account,
					"debit": self.grand_total,
					"debit_in_account_currency": self.grand_total,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
				}, item=self)
			)

		return gl_entry

	def add_tax_gl_entries(self, gl_entries):
		# tax table gl entries
		for tax in self.get("taxes"):
			gl_entries.append(
				self.get_gl_dict({
					"account": tax.account_head,
					"debit": tax.tax_amount,
					"debit_in_account_currency": tax.tax_amount,
					"against": self.employee,
					"cost_center": self.cost_center,
					"against_voucher_type": self.doctype,
					"against_voucher": self.name
				}, item=tax)
			)

	def validate_account_details(self):
		if not self.cost_center:
			frappe.throw(_("Cost center is required to book an expense claim"))

		if self.is_paid:
			if not self.mode_of_payment:
				frappe.throw(_("Mode of payment is required to make a payment").format(self.employee))

	def calculate_total_amount(self):
		self.total_claimed_amount = 0
		self.total_sanctioned_amount = 0
		for d in self.get('expenses'):
			if self.approval_status == 'Rejected':
				d.sanctioned_amount = 0.0

			self.total_claimed_amount += flt(d.amount)
			self.total_sanctioned_amount += flt(d.sanctioned_amount)

	def calculate_taxes(self):
		self.total_taxes_and_charges = 0
		for tax in self.taxes:
			if tax.rate:
				tax.tax_amount = flt(self.total_sanctioned_amount) * flt(tax.rate/100)

			tax.total = flt(tax.tax_amount) + flt(self.total_sanctioned_amount)
			self.total_taxes_and_charges += flt(tax.tax_amount)

		self.grand_total = flt(self.total_sanctioned_amount) + flt(self.total_taxes_and_charges) - flt(self.total_advance_amount)

	def update_task(self):
		task = frappe.get_doc("Task", self.task)
		task.update_total_expense_claim()
		task.save()

	def validate_advances(self):
		self.total_advance_amount = 0
		for d in self.get("advances"):
			ref_doc = frappe.db.get_value("Employee Advance", d.employee_advance,
				["posting_date", "paid_amount", "claimed_amount", "advance_account"], as_dict=1)
			d.posting_date = ref_doc.posting_date
			d.advance_account = ref_doc.advance_account
			d.advance_paid = ref_doc.paid_amount
			d.unclaimed_amount = flt(ref_doc.paid_amount) - flt(ref_doc.claimed_amount)

			if d.allocated_amount and flt(d.allocated_amount) > flt(d.unclaimed_amount):
				frappe.throw(_("Row {0}# Allocated amount {1} cannot be greater than unclaimed amount {2}")
					.format(d.idx, d.allocated_amount, d.unclaimed_amount))

			self.total_advance_amount += flt(d.allocated_amount)

		if self.total_advance_amount:
			precision = self.precision("total_advance_amount")
			if flt(self.total_advance_amount, precision) > flt(self.total_claimed_amount, precision):
				frappe.throw(_("Total advance amount cannot be greater than total claimed amount"))

			if self.total_sanctioned_amount \
					and flt(self.total_advance_amount, precision) > flt(self.total_sanctioned_amount, precision):
				frappe.throw(_("Total advance amount cannot be greater than total sanctioned amount"))

	def validate_sanctioned_amount(self):
		for d in self.get('expenses'):
			if flt(d.sanctioned_amount) > flt(d.amount):
				frappe.throw(_("Sanctioned Amount cannot be greater than Claim Amount in Row {0}.").format(d.idx))

	def set_expense_account(self, validate=False):
		for expense in self.expenses:
			if not expense.default_account or not validate:
				expense.default_account = get_expense_claim_account(expense.expense_type, self.company)["account"]

def update_reimbursed_amount(doc):
	amt = frappe.db.sql("""select ifnull(sum(debit_in_account_currency), 0) as amt
		from `tabGL Entry` where against_voucher_type = 'Expense Claim' and against_voucher = %s
		and party = %s """, (doc.name, doc.employee) ,as_dict=1)[0].amt

	doc.total_amount_reimbursed = amt
	frappe.db.set_value("Expense Claim", doc.name , "total_amount_reimbursed", amt)

	doc.set_status()
	frappe.db.set_value("Expense Claim", doc.name , "status", doc.status)

@frappe.whitelist()
def make_bank_entry(dt, dn):
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

	expense_claim = frappe.get_doc(dt, dn)
	default_bank_cash_account = get_default_bank_cash_account(expense_claim.company, "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(expense_claim.company, "Cash")

	payable_amount = flt(expense_claim.total_sanctioned_amount) \
		- flt(expense_claim.total_amount_reimbursed) - flt(expense_claim.total_advance_amount)

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = 'Bank Entry'
	je.company = expense_claim.company
	je.remark = 'Payment against Expense Claim: ' + dn;

	je.append("accounts", {
		"account": expense_claim.payable_account,
		"debit_in_account_currency": payable_amount,
		"reference_type": "Expense Claim",
		"party_type": "Employee",
		"party": expense_claim.employee,
		"reference_name": expense_claim.name
	})

	je.append("accounts", {
		"account": default_bank_cash_account.account,
		"credit_in_account_currency": payable_amount,
		"reference_type": "Expense Claim",
		"reference_name": expense_claim.name,
		"balance": default_bank_cash_account.balance,
		"account_currency": default_bank_cash_account.account_currency,
		"account_type": default_bank_cash_account.account_type
	})

	return je.as_dict()

@frappe.whitelist()
def get_expense_claim_account(expense_claim_type, company):
	account = frappe.db.get_value("Expense Claim Account",
		{"parent": expense_claim_type, "company": company}, "default_account")
	if not account:
		frappe.throw(_("Please set default account in Expense Claim Type {0}")
			.format(expense_claim_type))

	return {
		"account": account
	}

@frappe.whitelist()
def get_advances(employee, advance_id=None):
	if not advance_id:
		condition = 'docstatus=1 and employee={0} and paid_amount > 0 and paid_amount > claimed_amount + return_amount'.format(frappe.db.escape(employee))
	else:
		condition = 'name={0}'.format(frappe.db.escape(advance_id))

	return frappe.db.sql("""
		select
			name, posting_date, paid_amount, claimed_amount, advance_account
		from
			`tabEmployee Advance`
		where {0}
	""".format(condition), as_dict=1)


@frappe.whitelist()
def get_expense_claim(
	employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount):
	default_payable_account = frappe.get_cached_value('Company',  company,  "default_payable_account")
	default_cost_center = frappe.get_cached_value('Company',  company,  'cost_center')

	expense_claim = frappe.new_doc('Expense Claim')
	expense_claim.company = company
	expense_claim.employee = employee_name
	expense_claim.payable_account = default_payable_account
	expense_claim.cost_center = default_cost_center
	expense_claim.is_paid = 1 if flt(paid_amount) else 0
	expense_claim.append(
		'advances',
		{
			'employee_advance': employee_advance_name,
			'posting_date': posting_date,
			'advance_paid': flt(paid_amount),
			'unclaimed_amount': flt(paid_amount) - flt(claimed_amount),
			'allocated_amount': flt(paid_amount) - flt(claimed_amount)
		}
	)

	return expense_claim

@frappe.whitelist()
def create_expense_claim(user, expense_date, expense_claim_type, description, amount, project = None):
	"""
	API endpoint for creating expense claims for employees.

	Args:
		user (string): user_id of an Employee
		expense_date (date): Date when the expense were made
		expense_claim_type (string): Type of expense claim i.e. Calls, Food, Travel, Others, Vehicle, Medical
		description (string): Complete detail of the expense claim like 'Why the user is applying, is that claim covers in company policy etc'
		amount (number): Total amount that user wants to claim
	Return:
		nothing
	"""
	employee = frappe.get_doc("Employee", {"user_id": user})

	expense_approver = ""
	# Fetch list of expense approvers based on the department of the employee claiming the expense
	if employee.department:
		expense_approver = get_approvers("User", "", "name", 0, 100,{"employee": employee.name, "department": employee.department, "doctype": employee.doctype})
		if not expense_approver:
			expense_approver = ""
		else:
			expense_approver = [expense_approver[0] for expense_approver in expense_approver]
			# Randomly selecting the expense_approver from the expense_approver list.
			expense_approver = expense_approver[os.urandom(1)[0] % len(expense_approver)]

	# Creating expense claim doc.
	frappe.get_doc({
		"doctype": "Expense Claim",
		"employee": employee.name,
		"payable_account": frappe.get_value('Company', employee.company, 'default_payable_account'),
		"expense_approver": expense_approver,
		"project" : project,
		"expenses": [
			{
				"expense_date": expense_date,
				"expense_type": expense_claim_type,
				"amount": amount,
				"description": description
			}
		]
	}).insert(ignore_permissions=True, ignore_mandatory=True)
	return True

@frappe.whitelist()
def list_expense_claims(user,filters=None):
	"""
	API endpoint to get all Expense Claim list and its child table

	user: email id args required to list existing data created by that perticular user (Request From Driver App).
	filters: used to filter out the data while fetching (Optional)
	ex:
	{
		"user": "admin@bloomstack.com",
		"filters":"{\"expense_date\":[\">\",\"2020-10-1\"],\"expense_date\": [\"<\",\"2020-12-31\"]}" --> used as Between Filter for date
	}
	"""

	employee = frappe.db.exists("Employee", {"company_email": user})
	if not employee:
		return return_error_message_dict(_("Employee's E-mail ID Not Found, Please Add 'Company Email' Under 'Employee' Document"))

	if filters:
		filters = json.loads(filters)
		filters = {"employee": employee, **filters}
	else:
		filters = {"employee": employee}

	expense_claims = frappe.get_all("Expense Claim",filters = filters ,
		fields=["name", "employee_name", "approval_status", "expense_approver", "project", "`tabExpense Claim Detail`.*"])

	if not expense_claims:
		 return return_error_message_dict(_("No Claim Found for {0}.").format(user))

	return expense_claims

@frappe.whitelist()
def update_expense_claim(expense_claim_detail, expense_date=None, expense_claim_type=None, description=None, amount=None):
	"""
	API endpoint to update the existing data of given Expense Claim
	args:
	expense_claim_detail: Expense Claim Details ID to upddate perticular child data (This Data Can be found in 'list_expense_claims' api as 'name' key)
	expense_date: updated date, (Optional)
	expense_claim_type: updated claim type, (Optional)
	description: updated Description, (Optional)
	amount: updated Amount, (Optional)
	"""

	expense_claim_detail = frappe.get_doc("Expense Claim Detail", expense_claim_detail)
	if expense_claim_detail.docstatus == 1:
		return return_error_message_dict(_("Expense Claim '{0}' is submitted Document, It cannot be Updated").format(expense_claim_detail.parent))
	if expense_date:
		expense_claim_detail.update({"expense_date":expense_date})
	if description:
		expense_claim_detail.update({"description":description})
	if expense_claim_type:
		expense_claim_detail.update({"expense_claim_type":expense_claim_type})
	if amount:
		expense_claim_detail.update({"amount":amount})
	expense_claim_detail.save()
	return expense_claim_detail

@frappe.whitelist()
def delete_expense_claim(expense_claim):
	"""
	This API endpoint will delete the given Expense Claim
	args:
	expense_claim: Expense Claim unique Name to identify ex: 'HR-EXP-2021-XXXXX'
	"""

	if not frappe.db.exists("Expense Claim", expense_claim):
		return return_error_message_dict(_("'{0}' Not Found").format(expense_claim))

	expense_claim_doc = frappe.get_doc("Expense Claim", expense_claim)

	if expense_claim_doc.docstatus == 1:
		return return_error_message_dict(_("Expense Claim '{0}' is submitted Document, It cannot be Deleted").format(expense_claim))

	expense_claim_doc.delete()

	return return_error_message_dict(_("Expense Claim '{0}' is deleted").format(expense_claim))

def return_error_message_dict(message):
	return {"error": {"message": message}}