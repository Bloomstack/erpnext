import frappe
from frappe.core.utils import find


def get_default_license(party_type, party_name):
	"""
	Get default license from customer or supplier

	Args:
		party_type (str): The party DocType
		party_name (str): The party name

	Returns:
		str: The default license for the party, if any, otherwise None.
	"""

	if not (party_type and party_name):
		return

	party = frappe.get_doc(party_type, party_name)
	licenses = party.get("licenses")
	if not licenses:
		return

	default_license = find(licenses, lambda l: l.get("is_default")) or ''
	if default_license:
		default_license = default_license.get("license")

	return default_license


@frappe.whitelist()
def filter_license(doctype, txt, searchfield, start, page_len, filters):
	"""filter license"""

	return frappe.get_all('Compliance License Detail',
		filters={'parent': filters.get("party_name")},
		fields=["license", "is_default", "license_type"],
		as_list=1)
