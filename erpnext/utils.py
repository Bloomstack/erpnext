import json
import frappe
from frappe.utils import get_url, date_diff, get_time, getdate, to_timedelta, today
from frappe import _

@frappe.whitelist()
def get_contact(doctype, name, contact_field):

	contact = frappe.db.get_value(doctype, name, contact_field)

	contact_persons = frappe.db.sql(
		"""
			SELECT parent,
				(SELECT is_primary_contact FROM tabContact c WHERE c.name = dl.parent) AS is_primary_contact
			FROM
				`tabDynamic Link` dl
			WHERE
				dl.link_doctype=%s
				AND dl.link_name=%s
				AND dl.parenttype = "Contact"
		""", (frappe.unscrub(contact_field), contact), as_dict=1)

	if contact_persons:
		for contact_person in contact_persons:
			contact_person.email_id = frappe.db.get_value("Contact", contact_person.parent, ["email_id"])
			if contact_person.is_primary_contact:
				return contact_person

		contact_person = contact_persons[0]

		return contact_person

@frappe.whitelist()
def get_document_links(doctype, docs):
	docs = json.loads(docs)
	print_format = "print_format"
	links = []
	for doc in docs:
		link = frappe.get_template("templates/emails/print_link.html").render({
			"url": get_url(),
			"doctype": doctype,
			"name": doc.get("name"),
			"print_format": print_format,
			"key": frappe.get_doc(doctype, doc.get("name")).get_signature()
		})
		links.append(link)
	return links

@frappe.whitelist()
def create_authorization_request(dt, dn, contact_email, contact_name):
	new_authorization_request = frappe.new_doc("Authorization Request")
	new_authorization_request.linked_doctype = dt
	new_authorization_request.linked_docname = dn
	new_authorization_request.authorizer_email = contact_email
	new_authorization_request.authorizer_name = contact_name
	new_authorization_request.save()

@frappe.whitelist()
def login_as(user):
	# only these roles allowed to use this feature
	if any(True for role in frappe.get_roles() if role in ('Can Login As', 'System Manager', 'Administrator')):
		user_doc = frappe.get_doc("User", user)

		# only administrator can login as a system user
		if not("Administrator" in frappe.get_roles()) and user_doc and user_doc.user_type == "System User":
			return False

		frappe.local.login_manager.login_as(user)
		frappe.set_user(user)

		frappe.db.commit()
		frappe.local.response["redirect_to"] = '/'
		return True

	return False

@frappe.whitelist()
def create_contract_from_quotation(source_name, target_doc=None):
	existing_contract = frappe.db.exists("Contract", {"document_type": "Quotation", "document_name": source_name})
	if existing_contract:
		contract_link = frappe.utils.get_link_to_form("Contract", existing_contract)
		frappe.throw("A Contract already exists for this Quotation at {0}".format(contract_link))

	contract = frappe.new_doc("Contract")
	contract.party_name = frappe.db.get_value("Quotation", source_name, "party_name")
	contract.document_type = "Quotation"
	contract.document_name = source_name
	return contract

def validate_default_license(doc, method):
	"""allow to set only one default license for supplier or customer"""

	# remove duplicate licenses
	unique_licenses = list(set([license.license for license in doc.licenses]))
	if len(doc.licenses) != len(unique_licenses):
		frappe.throw(_("Please remove duplicate licenses before proceeding"))

	if len(doc.licenses) == 1:
		# auto-set default license if only one is found
		doc.licenses[0].is_default = 1
	elif len(doc.licenses) > 1:
		default_licenses = [license for license in doc.licenses if license.is_default]
		# prevent users from setting multiple default licenses
		if not default_licenses:
			frappe.throw(_("There must be atleast one default license, found none"))
		elif len(default_licenses) > 1:
			frappe.throw(_("There can be only one default license for {0}, found {1}").format(doc.name, len(default_licenses)))


def validate_expired_licenses(doc, method):
	"""remove expired licenses from company, customer and supplier records"""

	for row in doc.licenses:
		if row.license_expiry_date and row.license_expiry_date < getdate(today()):
			expired_since = date_diff(getdate(today()), getdate(row.license_expiry_date))
			frappe.msgprint(_("Row #{0}: License {1} has expired {2} days ago".format(
				row.idx, frappe.bold(row.license), frappe.bold(expired_since))))

def validate_delivery_window(doc, method):
	from erpnext.stock.doctype.delivery_trip.delivery_trip import get_delivery_window
	if not frappe.db.get_single_value("Delivery Settings", "send_delivery_window_warning"):
		return

	if not (doc.get("delivery_start_time") and doc.get("delivery_end_time")):
		return

	if not doc.get("customer"):
		return

	delivery_window = get_delivery_window(customer=doc.get("customer"))
	delivery_start_time = delivery_window.delivery_start_time
	delivery_end_time = delivery_window.delivery_end_time

	if not (delivery_start_time and delivery_end_time):
		return

	if to_timedelta(doc.delivery_start_time) < to_timedelta(delivery_start_time) \
		or to_timedelta(doc.delivery_end_time) > to_timedelta(delivery_end_time):
		if method == "validate":
			frappe.msgprint(_("The delivery window is set outside the customer's default timings"))
		elif method == "on_submit":
			# send an email notifying users that the document is outside the customer's delivery window
			role_profiles = ["Fulfillment Manager"]
			role_profile_users = frappe.get_all("User", filters={"role_profile_name": ["IN", role_profiles]}, fields=["email"])
			role_profile_users = [user.email for user in role_profile_users]

			accounts_managers = get_users_with_role("Accounts Manager")
			system_managers = get_users_with_role("System Manager")

			recipients = list(set(role_profile_users + accounts_managers) - set(system_managers))

			if not recipients:
				return

			# form the email
			subject = _("[Info] An order may be delivered outside a customer's preferred delivery window")
			message = _("""An order ({name}) has the following delivery window: {doc_start} - {doc_end}<br><br>
				While the default delivery window is {customer_start} - {customer_end}""".format(
					name=frappe.utils.get_link_to_form(doc.doctype, doc.name),
					doc_start=get_time(doc.delivery_start_time).strftime("%I:%M %p"),
					doc_end=get_time(doc.delivery_end_time).strftime("%I:%M %p"),
					customer_start=get_time(delivery_start_time).strftime("%I:%M %p"),
					customer_end=get_time(delivery_end_time).strftime("%I:%M %p"),
				))

			frappe.sendmail(recipients=recipients, subject=subject, message=message)

def get_users_with_role(role):
	# returns users with the specified role
	user_list = frappe.get_all("User", fields=["`tabUser`.name"],
		filters = [
				["Has Role", "role", "=", role],
				["User", "name", "not in", ["Guest", "Administrator"]],
				["User", "enabled", "=", 1]
			],
		as_list=1
	)

	return [user for users in user_list for user in users]