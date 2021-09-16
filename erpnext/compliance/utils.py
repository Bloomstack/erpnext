import frappe
from frappe.core.utils import find
from frappe.utils.background_jobs import enqueue
from frappe.utils.nestedset import get_root_of
from frappe.utils import get_host_name
from erpnext.compliance.doctype.compliance_info.compliance_info import make_bloomstack_site_license
from frappe.frappeclient import FrappeClient, AuthError
import json
from python_metrc import METRC


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

# bloomstack_core/compliance/settings.py code moved here

METRC_UOMS = {
	"Each": "Each",
	"Fluid Ounces": "Fluid Ounce (US)",
	"Gallons": "Gallon Liquid (US)",
	"Grams": "Gram",
	"Kilograms": "Kg",
	"Liters": "Litre",
	"Milligrams": "Milligram",
	"Milliliters": "Millilitre",
	"Ounces": "Ounce",
	"Pints": "Pint, Liquid (US)",
	"Pounds": "Pound",
	"Quarts": "Quart Liquid (US)"
}


@frappe.whitelist()
def sync_data():
	enqueue(pull_item_categories_from_bloomtrace)
	enqueue(pull_uoms_from_bloomtrace)

def pull_item_categories_from_bloomtrace():
	"""
	Pull METRC Item categories into Bloomstack from Bloomtrace.
	"""

	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return

	categories = frappe_client.get_list("Compliance Item Category", fields=["*"])

	create_root_element_if_not_exists()

	for category in categories:
		# Create Item Group for the METRC category
		if not frappe.db.exists("Item Group", category.get("name")):
			item_group = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": category.get("name"),
				"parent_item_group": "METRC Categories"
			})
			# Item groups cannot be the same name as an Item
			try:
				item_group.insert()
			except frappe.NameError:
				continue
		else:
			item_group = frappe.get_doc("Item Group", category.get("name"))

		# Create METRC Item Category
		if frappe.db.exists("Compliance Item Category", category.get("name")):
			doc = frappe.get_doc("Compliance Item Category", category.get("name"))
		else:
			doc = frappe.new_doc("Compliance Item Category")

		doc.update({
			"category_name": category.get("name"),
			"item_group": item_group.name,
			"product_category_type": category.get("product_category_type"),
			"quantity_type": category.get("quantity_type"),
			"mandatory_unit": category.get("mandatory_unit"),
			"strain_mandatory": category.get("strain_mandatory")
		}).save()


def pull_uoms_from_bloomtrace():
	"""
	Pull METRC Item UOMs into Bloomstack from Bloomtrace.
	"""

	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return

	uoms = frappe_client.get_list("Compliance UOM", fields=["*"])

	for uom in uoms:
		if frappe.db.exists("Compliance UOM", uom.get("name")):
			metrc_uom = frappe.get_doc("Compliance UOM", uom.get("name"))
		else:
			metrc_uom = frappe.new_doc("Compliance UOM")

		metrc_uom.update({
			"uom_name": uom.get("name"),
			"uom": METRC_UOMS.get(uom.get("name")),
			"abbreviation": uom.get("abbreviation"),
			"quantity_type": uom.get("quantity_type")
		}).save()


def create_root_element_if_not_exists():
	# Create root METRC item group
	if not frappe.db.exists("Item Group", "METRC Categories"):
		item_group = frappe.get_doc({
			"doctype": "Item Group",
			"item_group_name": "METRC Categories",
			"parent_item_group": get_root_of("Item Group"),
			"is_group": 1
		}).insert()


# bloomtrace/utils.py code moved here

def get_bloomtrace_client():
	url = frappe.conf.get("bloomtrace_server")
	username = frappe.conf.get("bloomtrace_username")
	password = frappe.conf.get("bloomtrace_password")

	if not url:
		return

	try:
		client = FrappeClient(url, username=username, password=password, verify=True)
	except ConnectionError:
		return
	except AuthError:
		return

	return client


def make_integration_request(doctype, docname, endpoint):
	settings = frappe.get_cached_doc("Compliance Settings")
	if not (frappe.conf.enable_bloomtrace and settings.is_compliance_enabled) or \
		frappe.db.exists("Integration Request", {"reference_doctype": doctype, "reference_docname": docname, "endpoint": endpoint}):
		return

	doc = frappe.get_doc(doctype, docname)
	company = settings.get("company", {"company": doc.company}) and settings.get("company", {"company": doc.company})[0]
	fieldname = "push_{0}".format(frappe.scrub(endpoint))

	if not company or not company.get(fieldname):
		return

	integration_request = frappe.get_doc({
		"doctype": "Integration Request",
		"integration_type": "Remote",
		"integration_request_service": "BloomTrace",
		"status": "Queued",
		"reference_doctype": doctype,
		"reference_docname": docname,
		"endpoint": endpoint
	}).save(ignore_permissions=True)


def create_integration_request(doc, method):
	make_integration_request(doc.doctype, doc.name)

def get_metrc():
	settings = frappe.get_single("Compliance Settings")

	if not settings.is_compliance_enabled:
		return

	if not all([settings.metrc_url, settings.metrc_vendor_key, settings.metrc_user_key, settings.metrc_vendor_key]):
		frappe.throw("Please configure Compliance Settings")

	return METRC(settings.metrc_url, settings.get_password("metrc_vendor_key"), settings.get_password("metrc_user_key"), settings.metrc_license_no)


def log_request(endpoint, request_data, response, ref_dt=None, ref_dn=None):
	request = frappe.new_doc("API Request Log")
	request.update({
		"endpoint": endpoint,
		"request_body": json.dumps(request_data, indent=4, sort_keys=True),
		"response_code": response.status_code,
		"response_body": json.dumps(response.text, indent=4, sort_keys=True),
		"reference_doctype": ref_dt,
		"reference_document": ref_dn
	})
	request.insert()
	frappe.db.commit()

@frappe.whitelist()
def create_purchase_receipt(transfer):
	transfer = frappe.parse_json(transfer)

	for item in transfer.get("items", []):
		supplier_item = frappe.db.get_all("Item Supplier", filters={"supplier_part_no": item.get("product_name")}, fields=["parent"])
		item.update({
			"item_code": supplier_item[0].parent if supplier_item else None,
			"metrc_product_name": item.get("product_name")
		})

	doc = frappe.get_doc({"doctype": "Purchase Receipt"})
	doc.update(transfer)
	doc.flags.ignore_validate=True
	doc.flags.ignore_mandatory=True
	doc.flags.ignore_links=True
	doc.insert()

def sync_with_bloomtrace():
	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return
	site_url = get_host_name()

	clear_bloomstack_site_users(frappe_client, site_url)
	make_bloomstack_site_users()

	clear_bloomstack_site_licenses(frappe_client, site_url)
	make_bloomstack_site_licenses(frappe_client, site_url)


def clear_bloomstack_site_users(frappe_client, site_url):
	bloomstack_site_user = frappe_client.get_doc("Bloomstack Site User", filters={"bloomstack_site": site_url})
	for user in bloomstack_site_user:
		frappe_client.delete("Bloomstack Site User", user.get('name'))


def make_bloomstack_site_users():
	for user in frappe.get_all("User"):
		frappe.get_doc("User", user.name).save()


def clear_bloomstack_site_licenses(frappe_client, site_url):
	bloomstack_site_license = frappe_client.get_doc("Bloomstack Site License", filters={"bloomstack_site": site_url})
	for site_license in bloomstack_site_license:
		frappe_client.delete("Bloomstack Site License", site_license.get('name'))


def make_bloomstack_site_licenses(frappe_client, site_url):
	compliance_info = frappe.get_all("Compliance Info")
	for site_license in compliance_info:
		license_info = frappe_client.get_doc("License Info", site_license.name)
		if license_info:
			make_bloomstack_site_license(frappe_client, site_url, site_license.name)