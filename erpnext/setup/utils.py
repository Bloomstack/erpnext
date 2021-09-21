# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, add_days
from frappe.utils import get_datetime_str, nowdate
from erpnext import get_default_company

def get_root_of(doctype):
	"""Get root element of a DocType with a tree structure"""
	result = frappe.db.sql_list("""select name from `tab%s`
		where lft=1 and rgt=(select max(rgt) from `tab%s` where docstatus < 2)""" %
		(doctype, doctype))
	return result[0] if result else None

def get_ancestors_of(doctype, name):
	"""Get ancestor elements of a DocType with a tree structure"""
	lft, rgt = frappe.db.get_value(doctype, name, ["lft", "rgt"])
	result = frappe.db.sql_list("""select name from `tab%s`
		where lft<%s and rgt>%s order by lft desc""" % (doctype, "%s", "%s"), (lft, rgt))
	return result or []

def before_tests():
	frappe.clear_cache()
	# complete setup if missing
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
	if not frappe.get_list("Company"):
		setup_complete({
			"currency"			:"USD",
			"full_name"			:"Test User",
			"company_name"		:"Wind Power LLC",
			"timezone"			:"America/New_York",
			"company_abbr"		:"WP",
			"industry"			:"Manufacturing",
			"country"			:"United States",
			"fy_start_date"		:"2011-01-01",
			"fy_end_date"		:"2011-12-31",
			"language"			:"english",
			"company_tagline"	:"Testing",
			"email"				:"test@erpnext.com",
			"password"			:"test",
			"chart_of_accounts" : "Standard",
			"domains"			: ["Manufacturing"],
		})

	frappe.db.sql("delete from `tabLeave Allocation`")
	frappe.db.sql("delete from `tabLeave Application`")
	frappe.db.sql("delete from `tabSalary Slip`")
	frappe.db.sql("delete from `tabItem Price`")

	frappe.db.set_value("Stock Settings", None, "auto_insert_price_list_rate_if_missing", 0)
	enable_all_roles_and_domains()

	frappe.db.commit()

@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, transaction_date=None, args=None):
	if not (from_currency and to_currency):
		# manqala 19/09/2016: Should this be an empty return or should it throw and exception?
		return
	if from_currency == to_currency:
		return 1

	if not transaction_date:
		transaction_date = nowdate()
	currency_settings = frappe.get_doc("Accounts Settings").as_dict()
	allow_stale_rates = currency_settings.get("allow_stale")

	filters = [
		["date", "<=", get_datetime_str(transaction_date)],
		["from_currency", "=", from_currency],
		["to_currency", "=", to_currency]
	]

	if args == "for_buying":
		filters.append(["for_buying", "=", "1"])
	elif args == "for_selling":
		filters.append(["for_selling", "=", "1"])

	if not allow_stale_rates:
		stale_days = currency_settings.get("stale_days")
		checkpoint_date = add_days(transaction_date, -stale_days)
		filters.append(["date", ">", get_datetime_str(checkpoint_date)])

	# cksgb 19/09/2016: get last entry in Currency Exchange with from_currency and to_currency.
	entries = frappe.get_all(
		"Currency Exchange", fields=["exchange_rate"], filters=filters, order_by="date desc",
		limit=1)
	if entries:
		return flt(entries[0].exchange_rate)

	try:
		cache = frappe.cache()
		key = "currency_exchange_rate_{0}:{1}:{2}".format(transaction_date,from_currency, to_currency)
		value = cache.get(key)

		if not value:
			import requests
			api_url = "https://frankfurter.app/{0}".format(transaction_date)
			response = requests.get(api_url, params={
				"base": from_currency,
				"symbols": to_currency
			})
			# expire in 6 hours
			response.raise_for_status()
			value = response.json()["rates"][to_currency]
			cache.setex(key, value, 6 * 60 * 60)
		return flt(value)
	except:
		frappe.log_error(title="Get Exchange Rate")
		frappe.msgprint(_("Unable to find exchange rate for {0} to {1} for key date {2}. Please create a Currency Exchange record manually").format(from_currency, to_currency, transaction_date))
		return 0.0

def enable_all_roles_and_domains():
	""" enable all roles and domain for testing """
	# add all roles to users
	domains = frappe.get_all("Domain")
	if not domains:
		return

	from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to
	frappe.get_single('Domain Settings').set_active_domains(\
		[d.name for d in domains])
	add_all_roles_to('Administrator')


def insert_record(records):
	for r in records:
		doc = frappe.new_doc(r.get("doctype"))
		doc.update(r)
		try:
			doc.insert(ignore_permissions=True)
		except frappe.DuplicateEntryError as e:
			# pass DuplicateEntryError and continue
			if e.args and e.args[0]==doc.doctype and e.args[1]==doc.name:
				# make sure DuplicateEntryError is for the exact same doc and not a related doc
				pass
			else:
				raise

def welcome_email():
	site_name = get_default_company() or "Bloomstack"
	title = _("Welcome to {0}").format(site_name)
	return title

@frappe.whitelist(allow_guest=True)
def authorize_document(sign=None, signee=None, docname=None, party_business_type=None, designation=None):
	if frappe.db.exists("Authorization Request", docname):
		authorization_request = frappe.get_doc("Authorization Request", docname)
		authorization_request.signature = sign
		authorization_request.signee_name = signee
		authorization_request.party_business_type = party_business_type
		authorization_request.designation = designation
		authorization_request.status = "Approved"
		authorization_request.flags.ignore_permissions = True
		authorization_request.save()

		authorized_doc = frappe.get_doc(authorization_request.linked_doctype, authorization_request.linked_docname)
		if hasattr(authorized_doc, "is_signed") and \
			 hasattr(authorized_doc, "customer_signature") and \
			 hasattr(authorized_doc, "signee") and \
			 hasattr(authorized_doc, "party_business_type") and \
			 hasattr(authorized_doc, "designation"):
			if authorized_doc.is_signed == 0:
				authorized_doc.is_signed = 1
				authorized_doc.customer_signature = sign
				authorized_doc.signee = signee
				authorized_doc.party_business_type = party_business_type
				authorized_doc.designation = designation
				authorized_doc.signed_on = frappe.utils.now()

		authorized_doc.flags.ignore_permissions = True
		authorized_doc.submit()

		email_authorized_doc(docname)

def email_authorized_doc(authorization_request_name):
	authorization_request = frappe.get_doc("Authorization Request", authorization_request_name)
	authorized_doc = frappe.get_doc(authorization_request.linked_doctype, authorization_request.linked_docname)
	recipients = [authorization_request.authorizer_email]
	company = authorized_doc.company if hasattr(authorized_doc, 'company') else get_default_company()
	subject = "Your signed {0} with {1}".format(authorized_doc.doctype, company)
	message = frappe.render_template("templates/emails/authorization_request.html", {
			"authorization_request": authorization_request,
			"company": company,
			"linked_doc": authorized_doc
		})
	print_format = "Bloomstack Contract" if authorized_doc.doctype == 'Contract' else "Standard"
	attachments = [frappe.attach_print(authorized_doc.doctype, authorized_doc.name, print_format=print_format)]
	frappe.sendmail(recipients=recipients, attachments=attachments, subject=subject, message=message)

@frappe.whitelist(allow_guest=True)
def reject_document(docname):
	if frappe.db.exists("Authorization Request", docname):
		authorization_request = frappe.get_doc("Authorization Request", docname)
		authorization_request.status = "Rejected"
		authorization_request.save()