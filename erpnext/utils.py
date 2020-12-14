import json
import frappe
from frappe.utils import get_url

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
