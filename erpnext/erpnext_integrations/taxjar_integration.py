import traceback

import pycountry
import taxjar
import json
import frappe
from erpnext import get_default_company
from frappe import _
from frappe.utils import cint, flt, get_link_to_form
from frappe.contacts.doctype.address.address import get_company_address
from frappe.integrations.utils import make_integration_request, update_integration_request

SUPPORTED_COUNTRY_CODES = ["AT", "AU", "BE", "BG", "CA", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
	"FR", "GB", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
	"SE", "SI", "SK", "US"]

class AddressError(frappe.ValidationError): pass

def get_client(doc):
	TAXJAR_ENABLED = frappe.db.get_value("TaxJar Configuration", doc.company, "enabled")

	if not TAXJAR_ENABLED:
		return

	taxjar_settings = frappe.get_doc("TaxJar Configuration", doc.company)

	if not taxjar_settings.is_sandbox:
		api_key = taxjar_settings.get_password("api_key")
		api_url = taxjar.DEFAULT_API_URL
	else:
		api_key = taxjar_settings.get_password("sandbox_api_key")
		api_url = taxjar.SANDBOX_API_URL

	if api_key and api_url:
		client = taxjar.Client(api_key=api_key, api_url=api_url)
		client.set_api_config('headers', {
			'x-api-version': '2020-08-07'
		})
		return client

def create_transaction(doc, method=None, backfill=False):
	"""Create an order transaction in TaxJar"""

	TAXJAR_CREATE_TRANSACTIONS = frappe.db.get_value("TaxJar Configuration", doc.company, "taxjar_create_transactions")
	TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "tax_account_head")

	if not TAXJAR_CREATE_TRANSACTIONS:
		return

	client = get_client(doc)

	if not client:
		return

	sales_tax = sum([tax.tax_amount for tax in doc.taxes if tax.account_head == TAX_ACCOUNT_HEAD])

	if not sales_tax:
		return

	tax_dict = get_tax_data(doc)

	if not tax_dict:
		return

	tax_dict['transaction_id'] = doc.name
	if not backfill:
		tax_dict['transaction_date'] = frappe.utils.today()
	else:
		tax_dict['transaction_date'] = frappe.utils.formatdate(doc.posting_date, 'yyyy/mm/dd')
	tax_dict['sales_tax'] = sales_tax
	tax_dict['amount'] = doc.net_total + tax_dict['shipping']

	integration_request = make_integration_request(doc.doctype, doc.name, service="TaxJar")
	try:
		if doc.is_return:
			update_integration_request(integration_request, endpoint="client.create_refund")
			tax_dict['transaction_reference_id'] = doc.return_against
			response = client.create_refund(tax_dict)
		else:
			update_integration_request(integration_request, endpoint="client.create_order")
			response = client.create_order(tax_dict)
	except taxjar.exceptions.TaxJarResponseError as err:
		doc.add_comment('Comment', _('TaxJar Create Transaction Failed. View Log > {0}').format(get_link_to_form("Integration Request", integration_request.name)))
		update_integration_request(integration_request, status="Failed", error=sanitize_error_response(err))
	else:
		doc.add_comment('Comment', _('TaxJar Create Transaction Completed. View Log > {0}').format(get_link_to_form("Integration Request", integration_request.name)))
		update_integration_request(integration_request, status="Completed", response=json.dumps(response.to_json()))
		if backfill:
			return True

def delete_transaction(doc, method):
	"""Delete an existing TaxJar order transaction"""

	TAXJAR_CREATE_TRANSACTIONS = frappe.db.get_value("TaxJar Configuration", doc.company, "taxjar_create_transactions")
	if not TAXJAR_CREATE_TRANSACTIONS:
		return

	client = get_client(doc)

	if not client:
		return

	integration_request = make_integration_request(doc.doctype, doc.name, service="TaxJar")
	try:
		if doc.is_return:
			update_integration_request(integration_request, endpoint="client.delete_refund")
			response = client.delete_refund(doc.name)
		else:
			update_integration_request(integration_request, endpoint="client.delete_order")
			response = client.delete_order(doc.name)
	except taxjar.exceptions.TaxJarResponseError as err:
		update_integration_request(integration_request, status="Failed", error=str(err))
	else:
		update_integration_request(integration_request, status="Completed", response=json.dumps(response.to_json()))

def update_transaction(doc, method=None, backfill=False):
	"""Create an order transaction in TaxJar"""

	TAXJAR_CREATE_TRANSACTIONS = frappe.db.get_value("TaxJar Configuration", doc.company, "taxjar_create_transactions")
	TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "tax_account_head")

	if not TAXJAR_CREATE_TRANSACTIONS:
		return

	client = get_client(doc)

	if not client:
		return

	taxjar_order = client.show_order(doc.name)
	if not taxjar_order:
		return

	sales_tax = sum([tax.tax_amount for tax in doc.taxes if tax.account_head == TAX_ACCOUNT_HEAD])

	if not sales_tax:
		return

	tax_dict = get_tax_data(doc)

	if not tax_dict:
		return

	tax_dict['transaction_id'] = doc.name
	if not backfill:
		tax_dict['transaction_date'] = frappe.utils.today()
	tax_dict['sales_tax'] = sales_tax
	tax_dict['amount'] = doc.net_total + tax_dict['shipping']

	integration_request = make_integration_request(doc.doctype, doc.name, service="TaxJar")
	try:
		if doc.is_return:
			update_integration_request(integration_request, endpoint="client.update_refund")
			tax_dict['transaction_reference_id'] = doc.return_against
			response = client.update_refund(doc.name, tax_dict)
		else:
			update_integration_request(integration_request, endpoint="client.update_order")
			response = client.update_order(doc.name, tax_dict)
	except taxjar.exceptions.TaxJarResponseError as err:
		doc.add_comment('Comment', _('TaxJar Update Transaction Failed. View Log > {0}').format(get_link_to_form("Integration Request", integration_request.name)))
		update_integration_request(integration_request, status="Failed", error=sanitize_error_response(err))
	else:
		doc.add_comment('Comment', _('TaxJar Update Transaction Completed. View Log > {0}').format(get_link_to_form("Integration Request", integration_request.name)))
		update_integration_request(integration_request, status="Completed", response=json.dumps(response.to_json()))
		if backfill:
			return True

def get_tax_data(doc):
	SHIP_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "shipping_account_head")
	from_address = get_company_address_details(doc)
	from_shipping_state = from_address.get("state")
	from_country_code = frappe.db.get_value("Country", from_address.country, "code")
	from_country_code = from_country_code.upper()

	to_address = get_shipping_address_details(doc)
	to_shipping_state = to_address.get("state")
	to_country_code = frappe.db.get_value("Country", to_address.country, "code")
	to_country_code = to_country_code.upper()

	if to_country_code not in SUPPORTED_COUNTRY_CODES:
		return

	shipping = sum([tax.tax_amount for tax in doc.taxes if tax.account_head == SHIP_ACCOUNT_HEAD])

	if to_shipping_state is not None:
		to_shipping_state = get_iso_3166_2_state_code(to_address)

	# for refund transaction send args as True so that we can maintain negative rate for refund transaction.
	line_items = [get_line_item_dict(item, doc, refund_transaction=doc.is_return) for item in doc.items]

	tax_dict = {
		'from_country': from_country_code,
		'from_zip': from_address.pincode,
		'from_state': from_shipping_state,
		'from_city': from_address.city,
		'from_street': from_address.address_line1,
		'to_country': to_country_code,
		'to_zip': to_address.pincode,
		'to_city': to_address.city,
		'to_street': to_address.address_line1,
		'to_state': to_shipping_state,
		'shipping': shipping,
		'amount': doc.net_total,
		'line_items': line_items,
		'plugin': 'bloomstack'
	}

	return tax_dict


def set_sales_tax(doc, method):
	TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "tax_account_head")
	TAXJAR_CALCULATE_TAX = frappe.db.get_value("TaxJar Configuration", doc.company, "taxjar_calculate_tax")
	if not TAXJAR_CALCULATE_TAX:
		return

	if not doc.items:
		return

	# if doctype is Quotation and it is created for lead set sales_tax_exempted to zero
	if doc.doctype == "Quotation" and doc.quotation_to == "Lead":
		sales_tax_exempted = hasattr(doc, "exempt_from_sales_tax") and doc.exempt_from_sales_tax \
			or frappe.db.has_column("Lead", "exempt_from_sales_tax") and frappe.db.get_value("Lead", doc.party_name, "exempt_from_sales_tax")
	# if the party is exempt from sales tax, then set all tax account heads to zero
	else:
		sales_tax_exempted = hasattr(doc, "exempt_from_sales_tax") and doc.exempt_from_sales_tax \
			or frappe.db.has_column("Customer", "exempt_from_sales_tax") and frappe.db.get_value("Customer", doc.customer, "exempt_from_sales_tax")

	if not TAX_ACCOUNT_HEAD:
		frappe.throw(_("Please add accounts in taxjar setting for company " + doc.company))

	if sales_tax_exempted:
		for tax in doc.taxes:
			if tax.account_head == TAX_ACCOUNT_HEAD:
				tax.tax_amount = 0
				break

		doc.run_method("calculate_taxes_and_totals")
		return

	tax_dict = get_tax_data(doc)

	if not tax_dict:
		# Remove existing tax rows if address is changed from a taxable state/country
		setattr(doc, "taxes", [tax for tax in doc.taxes if tax.account_head != TAX_ACCOUNT_HEAD])
		return

	# check if delivering within a nexus, if not, No need to call calculate sales tax api.
	has_nexus = check_for_nexus(doc, tax_dict)
	if not has_nexus:
		return

	tax_data = get_sales_tax(doc, tax_dict)

	if tax_data is not None:
		if not tax_data.amount_to_collect:
			setattr(doc, "taxes", [tax for tax in doc.taxes if tax.account_head != TAX_ACCOUNT_HEAD])
		elif tax_data.amount_to_collect > 0:
			# Loop through tax rows for existing Sales Tax entry
			# If none are found, add a row with the tax amount
			for tax in doc.taxes:
				if tax.account_head == TAX_ACCOUNT_HEAD:
					tax.tax_amount = tax_data.amount_to_collect

					doc.run_method("calculate_taxes_and_totals")
					break
			else:
				doc.append("taxes", {
					"category": "Total",
					"add_deduct_tax": "Add",
					"charge_type": "Actual",
					"description": "Sales Tax",
					"account_head": TAX_ACCOUNT_HEAD,
					"tax_amount": tax_data.amount_to_collect
				})

		for item in tax_data.breakdown.line_items:
			doc.get('items')[cint(item.id)-1].tax_collectable = item.tax_collectable
			doc.get('items')[cint(item.id)-1].taxable_amount = item.taxable_amount

		doc.run_method("calculate_taxes_and_totals")

def check_for_nexus(doc, tax_dict):
	"""
		IN the US we validate Nexus with State. for eg. if your shipping address state and Nexus state match then calculate Sales Tax.
		For Non-US countries like Australia if it is a different state still calculate Sales Tax Ref.https://developers.taxjar.com/demo/
		So apart from the US no other country has a state-based sales tax.

		Parameters:
			doc (dict): The doctype object from Quotation, Sales Order and Sales Invoice
			tax_dict(dict): The tax_dict contains tax data.

		Returns:
			Bool (True/False): based on output it will return flag
	"""

	#check if seller and buyer within same country otherwise dont calculate taxes
	if tax_dict["to_country"] == tax_dict["from_country"]:
		# if seller and buyer within US country then based on nexus region calculate tax
		if tax_dict["to_country"] == "US":
			# check if to_state within nexus region if not do not calculate sales tax.
			if not frappe.db.get_value('TaxJar Nexus', {'region_code': tax_dict["to_state"]}):
				return remove_existing_sales_tax(doc)
			return True

		# for Non-US country check if to_country within nexus country if not, do not calculate sales tax
		elif not frappe.db.get_value('TaxJar Nexus', {'country_code': tax_dict["to_country"]}):
			return remove_existing_sales_tax(doc)
		return True
	else:
		return remove_existing_sales_tax(doc)

def remove_existing_sales_tax(doc):
	"""
		Return False Boolean If buyer is not within nexus and if seller and buyer in different country. 
		it will delete taxes if any

		Parameters:
			doc (dict): The doctype object

		Returns:
			(bool): It always return False Boolean Value
	"""

	TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "tax_account_head")

	# Remove sales Tax amount from child level table
	for item in doc.get("items"):
		item.tax_collectable = flt(0)
		item.taxable_amount = flt(0)

	for tax in doc.taxes:
		if tax.account_head == TAX_ACCOUNT_HEAD:
			doc.taxes.remove(tax)
	return False

def get_sales_tax(doc, tax_dict):
	"""Return the sales tax that should be collected for a given order."""

	client = get_client(doc)

	if not client:
		return

	if doc.is_new():
		integration_request = make_integration_request(doc.doctype, None, service="TaxJar", endpoint="client.tax_for_order")
	else:
		integration_request = make_integration_request(doc.doctype, doc.name, service="TaxJar", endpoint="client.tax_for_order")
	try:
		tax_data = client.tax_for_order(tax_dict)
	except taxjar.exceptions.TaxJarResponseError as err:
		update_integration_request(integration_request, status="Failed", error=str(err))
		error_msg = """There seems to be an error in Address<br><br>{0}""".format(sanitize_error_response(err))
		frappe.throw(_(error_msg), AddressError, _("Address Error"))
	else:
		update_integration_request(integration_request, status="Completed", response=json.dumps(tax_data.to_json()))
		return tax_data


def get_company_address_details(doc):
	"""Return default company address details"""

	company_address = get_company_address(doc.company).company_address

	if not company_address:
		frappe.throw(_("Please set a default company address"))

	company_address = frappe.get_doc("Address", company_address)
	return company_address


def get_shipping_address_details(doc):
	"""Return customer shipping address details"""

	if doc.shipping_address_name:
		shipping_address = frappe.get_doc("Address", doc.shipping_address_name)
	else:
		shipping_address = get_company_address_details(doc)

	return shipping_address


def get_iso_3166_2_state_code(address):
	if not address.get("state"):
		return ""

	country_code = frappe.db.get_value("Country", address.get("country"), "code")

	error_message = _("""{0} is not a valid state! Check for typos or enter the ISO code for your state.""").format(address.get("state"))
	state = address.get("state").upper().strip()

	# The max length for ISO state codes is 3, excluding the country code
	if len(state) <= 3:
		# PyCountry returns state code as {country_code}-{state-code} (e.g. US-FL)
		address_state = (country_code + "-" + state).upper()

		states = pycountry.subdivisions.get(country_code=country_code.upper())
		states = [pystate.code for pystate in states]

		if address_state in states:
			return state

		frappe.throw(_(error_message))
	else:
		try:
			lookup_state = pycountry.subdivisions.lookup(state)
		except LookupError:
			frappe.throw(_(error_message))
		else:
			return lookup_state.code.split('-')[1]


def sanitize_error_response(response):
	response = response.full_response.get("detail")
	response = response.replace("_", " ")

	sanitized_responses = {
		"to zip": "Zipcode",
		"to city": "City",
		"to state": "State",
		"to country": "Country"
	}

	for k, v in sanitized_responses.items():
		response = response.replace(k, v)

	return response


def get_line_item_dict(item, doc, refund_transaction=False):
	line_item_discount = 0
	distributed_discount_percentage = 0
	distributed_discount = 0

	# this condition added to prevent item going to negative if distributed discount applied.
	if item.get("rate") > item.get("price_list_rate"):
		frappe.throw(_("Row.{0}: Item {1} Rate {2} should not be more than Price List Rate {3}".format(item.get('idx'), item.get('item_name'), item.get('rate'), item.get('price_list_rate'))))

	# line item discounting calculate
	if item.get("discount_percentage"):
		line_item_discount = (item.get("qty") * (item.get("price_list_rate") * item.get("discount_percentage"))/100)
	else:
		line_item_discount = item.get("discount_amount")

	# if paraent level discount aviliable then distribute to line item proportionally
	if doc.discount_amount:
		# Becuase of Taxjar need proportional discount distribution we added this formula.
		distributed_discount_percentage = (doc.discount_amount / (doc.discount_amount + doc.net_total)) * 100

		# below calculation, item.get("rate") is used instead of price_list_rate otherwise amount will go negative.
		distributed_discount = ((item.get("qty") * item.get("rate")) * distributed_discount_percentage) / 100

	return dict(
		id = item.get('idx'),
		description = item.get("item_name"),
		quantity = abs(item.get("qty")) if refund_transaction else item.get("qty"),
		unit_price = -abs(item.get("price_list_rate")) if refund_transaction else item.get("price_list_rate"),
		product_tax_code = item.get("product_tax_code"),
		sales_tax = item.get("tax_collectable"),
		discount = line_item_discount + distributed_discount
	) 
