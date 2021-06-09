# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
# Integrating Authorizenet

### 1. Validate Currency Support

Example:

	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"createTransactionRequest": {
			"merchantAuthentication": {
				"name": "xxxxxxxxxx",
				"transactionKey": "xxxxxxxxxxxx"
			},
			"refId": "123456",
			"transactionRequest": {
				"transactionType": "authCaptureTransaction",
				"amount": "5",
				"payment": {
					"credit_card": {
						"card_number": "XXXX-XXXX-XXXX-XXXX",
						"expiration_date": "YYYY-MM",
						"card_code": "XXX"
					}
				},
				"lineItems": {
					"lineItem": {
						"itemId": "1",
						"name": "vase",
						"description": "Cannes logo",
						"quantity": "18",
						"unitPrice": "45.00"
					}
				}
			}
		}
	}

	# redirect the user to this url
	url = controller().get_payment_url(**payment_details)

### 3. On Completion of Payment

Return payment status after processing the payment

"""

import json
import re
import datetime

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController, getUnsettledTransactionListController
from authorizenet.constants import constants
from six.moves.urllib.parse import urlencode

import frappe
from frappe import _
from frappe.integrations.utils import create_payment_gateway, create_request_log
from frappe.model.document import Document
from frappe.utils import call_hook_method, cstr, get_url, now
from frappe.utils.data import time_diff_in_seconds
from frappe.utils.password import get_decrypted_password
from erpnext.utilities.utils import retry


class AuthorizenetSettings(Document):
	supported_currencies = ["USD", "CAD"]

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. Authorizenet does not support transactions in currency '{0}'").format(currency))

	def validate(self):
		create_payment_gateway('Authorizenet')
		call_hook_method('payment_gateway_enabled', gateway="Authorizenet")

	def get_payment_url(self, **kwargs):
		return get_url("./integrations/authorizenet_checkout?{0}".format(urlencode(kwargs)))

def get_order_request_info(reference_doctype, reference_docname):
	"""Returns the latestt dict containing Integration Request name, status and errortext if one
	is found for the provided reference doctype and docname.

	Otherwise return False if no Integration Request is found.
	"""
	# Check if there was already a request for this api call
	# and return last attempt
	existing_requests = frappe.get_all(
		"Integration Request",
		fields=["name", "status", "error", "modified"],
		filters={
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
			"integration_request_service": "Authorizenet",
			"integration_type": "Host"
		},
		order_by="modified desc",
		limit=1
	)

	if len(existing_requests) > 0:
		request = existing_requests[0]
		return request

	return False

def query_successful_authnet_transaction(request):
	merchantAuth = request.merchant_auth or None
	order_ref = request.reference_doc.name
	amount = request.amount

	if merchantAuth is None:
		merchantAuth = apicontractsv1.merchantAuthenticationType()
		merchantAuth.name = frappe.db.get_single_value("Authorizenet Settings", "api_login_id")
		merchantAuth.transactionKey = get_decrypted_password('Authorizenet Settings', 'Authorizenet Settings',
			fieldname='api_transaction_key', raise_exception=False)

	# set sorting parameters
	sorting = apicontractsv1.TransactionListSorting()
	sorting.orderBy = apicontractsv1.TransactionListOrderFieldEnum.id
	sorting.orderDescending = True

	# set paging and offset parameters
	paging = apicontractsv1.Paging()
	# Paging limit can be up to 1000 for this request
	paging.limit = 20
	paging.offset = 1

	transactionListRequest = apicontractsv1.getTransactionListRequest()
	transactionListRequest.merchantAuthentication = merchantAuth
	transactionListRequest.refId = order_ref
	transactionListRequest.sorting = sorting
	transactionListRequest.paging = paging

	unsettledTransactionListController = getUnsettledTransactionListController(transactionListRequest)
	if not frappe.db.get_single_value("Authorizenet Settings", "sandbox_mode"):
		unsettledTransactionListController.setenvironment(constants.PRODUCTION)

	unsettledTransactionListController.execute()

	# Work on the response
	response = unsettledTransactionListController.getresponse()

	if response is not None and \
		response.messages.resultCode == apicontractsv1.messageTypeEnum.Ok and \
		hasattr(response, 'transactions'):
				for transaction in response.transactions.transaction:
					if (transaction.transactionStatus == "capturedPendingSettlement" or \
						transaction.transactionStatus == "authorizedPendingCapture") and \
						transaction.invoiceNumber == order_ref and transaction.amount == amount:
						return transaction
	return False

@frappe.whitelist()
def get_status(data):
	if isinstance(data, str):
		data = json.loads(data)
		data = frappe._dict(data)

	# sanity gate keeper. Don't process anything without reference doctypes
	if not data.reference_doctype or not data.reference_docname:
		return {
			"status": "Failed",
			"description": "Invalid request. Submitted data contains no order reference. This seems to be an internal error. Please contact support."
		}

	# fetch previous requests info
	request_info = get_order_request_info(data.reference_doctype, data.reference_docname)

	# and document references
	pr = frappe.get_doc(data.reference_doctype, data.reference_docname)
	reference_doc = frappe.get_doc(pr.reference_doctype, pr.reference_name)

	if request_info:
		status = request_info.get("status")
		integration_request = frappe.get_doc("Integration Request", request_info.name)

		if status == "Queued":
			# we don't want to wait forever for a failed request that never updated
			# the integration request status
			time_elapsed_since_update = time_diff_in_seconds(now(), request_info.modified)
			if time_elapsed_since_update < 60:
				return {
					"status": "Queued",
					"wait": 5000
				}
			else:
				# assume dropped request and flag as failed. Then restart call process with new
				# integration request.
				integration_request.error = "[Timeout] Integration Request lasted longer than 60 seconds. Assuming dropped request."
				integration_request.update_status(data, "Failed")
				integration_request = None
				early_exit = False
				return {
					"status": "Failed",
					"type": "ProcessorTimeout",
					"description": "Request to credit card processor Timed out."
				}
		elif status == "Completed":
			return {
				"status": "Completed"
			}

		if status == "Failed":
			if "declined" in (integration_request.error or "").lower():
				return {
					"status": "Failed",
					"type": "Validation",
					"description": integration_request.error
				}

			# don't early exit on failed. Means we are retrying a new card
			return {
				"status": "Failed",
				"type": "Unhandled",
				"description": integration_request.error
			}
	
	return {
		"status": "NotFound"
	}


@frappe.whitelist()
def charge_credit_card(card, data):
	"""
	Charge a credit card
	"""
	data = frappe._dict(json.loads(data))
	card = frappe._dict(json.loads(card))

	# sanity gate keeper. Don't process anything without reference doctypes
	if not data.reference_doctype or not data.reference_docname:
		return {
			"status": "Failed",
			"description": "Invalid request. Submitted data contains no order reference. This seems to be an internal error. Please contact support."
		}

	# fetch previous requests info
	request_info = get_order_request_info(data.reference_doctype, data.reference_docname)

	# and document references
	pr = frappe.get_doc(data.reference_doctype, data.reference_docname)
	reference_doc = frappe.get_doc(pr.reference_doctype, pr.reference_name)

	# Sanity check. Make sure to not process card if a previous request was fullfilled
	status = get_status(data)
	if status.get("status") != "Failed" and status.get("status") != "NotFound":
		return status

	# sanity gate keeper. Don't process anything without reference doctypes
	if not data.reference_doctype or not data.reference_docname:
		return {
			"status": "Failed",
			"description": "Invalid request. Submitted data contains no order reference. This seems to be an internal error. Please contact support."
		}

	# fetch previous requests info
	request_info = get_order_request_info(data.reference_doctype, data.reference_docname)

	# and document references
	pr = frappe.get_doc(data.reference_doctype, data.reference_docname)
	reference_doc = frappe.get_doc(pr.reference_doctype, pr.reference_name)

	# Sanity check. Make sure to not process card if a previous request was fullfilled
	status = get_status(data)
	if status.get("status") != "Failed" and status.get("status") != "NotFound":
		return status

	# Create Integration Request
	integration_request = create_request_log(data, "Host", "Authorizenet")

	# Setup Authentication on Authorizenet
	merchant_auth = apicontractsv1.merchantAuthenticationType()
	merchant_auth.name = frappe.db.get_single_value("Authorizenet Settings", "api_login_id")
	merchant_auth.transactionKey = get_decrypted_password('Authorizenet Settings', 'Authorizenet Settings',
		fieldname='api_transaction_key', raise_exception=False)

	# create request dict to ease passing around data
	request = frappe._dict({
		"pr": 	pr,
		"reference_doc": reference_doc,
		"data": data,
		"merchant_auth": merchant_auth,
		"integration_request": integration_request,
		"card": card
	})

	# Charge card step
	def tryChargeCard(i):
		# ping authnet first to check if transaction was previously made
		order_transaction = query_successful_authnet_transaction(request)

		# if transaction was already recorded on authnet side, update integration
		# request and return success
		if order_transaction:
			return frappe._dict({
				"status": "Completed"
			})

		# Otherwise, begine charging card
		response = authnet_charge(request)

		# translate result to response payload
		status = "Failed"
		if response is not None:
			# Check to see if the API request was successfully received and acted upon
			if response.messages.resultCode == "Ok" and hasattr(response.transactionResponse, 'messages') is True:
				status = "Completed"

		response_dict = to_dict(response)
		result = frappe._dict({
			"status": status
		})

		if status == "Completed":
			description = response_dict.get(
				"transactionResponse", {}) \
					.get("messages",{}) \
					.get("message", {}) \
					.get("description", "")

			if description:
				result.update({"description": description})

		elif status == "Failed":
			description = response_dict.get(
				"transactionResponse", {}) \
					.get("errors",{}) \
					.get("error", {}) \
					.get("errorText", "Unknown Error")

			if description:
				result.update({"description": description})

			integration_request.error = description
		else:
			# TODO: Check what errors would trickle here...
			result.update({
				"description": "Something went wrong while trying to complete the transaction. Please try again."
			})

		# update integration request with result
		integration_request.update_status(data, status)

		# Finally update PR and order
		if status != "Failed":
			try:
				pr.run_method("on_payment_authorized", status)
				# now update Payment Entry to store card holder name for record keeping
				pe_list = frappe.get_all("Payment Entry", filters={"reference_no": pr.name}, limit=1)
				if len(pe_list) > 0:
					pe_name = pe_list[0]
					remarks = frappe.db.get_value("Payment Entry", pe_name, "remarks")
					remarks = "{}\n---\nCard Holder: {}".format(remarks, card.holder_name)
					frappe.db.set_value("Payment Entry", pe_name, "remarks", remarks)
			except Exception as ex:
				# we have a payment, however an internal process broke
				# so, log it and add a comment on the reference document.
				# continue to process the request as if it was succesful
				traceback = frappe.get_traceback()
				err_doc = frappe.log_error(message=traceback , title="Error processing credit card")
				request.reference_doc.add_comment("Comment",
					text="[INTERNAL ERROR] There was a problem while processing this order's payment.\n"+
					"The transaction was record successfully and the card was charged.\n\n" +
					"However, please contact support to track down this issue and provide the following " +
					"error id: " + err_doc.name
				)

		# Flag declined transactions as a validation error which the user should correct.
		if "declined" in (result.get("description") or "").lower():
			result.type = "Validation"

		if "duplicate" in (result.get("description") or "").lower():
			result.type = "Duplicate"

		return result

	# validate result to trigger a retry or complete calls
	def chargeResultPredicate(result, i):
		return result

	# handle exceptions during card charges
	def chargeExceptionPredicate(exception, i):
		result_obj = {}

		if isinstance(exception, Exception):
			description = "There was an internal error while processing your payment." + \
				"To avoid double charges, please contact us."
			traceback = frappe.get_traceback()
			frappe.log_error(message=traceback , title="Error processing credit card")
			result_obj.update({
				"status": "Failed",
				"description": description,
				"error": exception.message
			})

		return result_obj

	result = retry(tryChargeCard, 3, chargeResultPredicate, chargeExceptionPredicate)

	return result

def authnet_charge(request):
	# data refs
	data = request.data
	card = request.card
	reference_doc = request.reference_doc

	# Create the payment data for a credit card
	credit_card = apicontractsv1.creditCardType()
	credit_card.cardNumber = request.card.number
	credit_card.expirationDate = request.card.expiration_date
	credit_card.cardCode = request.card.code

	# Add the payment data to a paymentType object
	payment = apicontractsv1.paymentType()
	payment.creditCard = credit_card

	# determin company name to attach to customer address record
	customer_name = None
	if reference_doc.doctype == "Quotation" and frappe.db.exists("Customer", reference_doc.party_name):
		# sanity test, only fetch customer record from party_name
		customer_name = reference_doc.party_name
	else:
		customer_name = reference_doc.customer

	name_parts = card.holder_name.split(None, 1)
	customer_address = apicontractsv1.customerAddressType()
	customer_address.firstName = name_parts[0] or data.payer_name
	customer_address.lastName = name_parts[1] if len(name_parts) > 1 else ""
	customer_address.email = card.holder_email or data.payer_email

	# setting billing address details
	if frappe.db.exists("Address", reference_doc.customer_address):
		address = frappe.get_doc("Address", reference_doc.customer_address)
		customer_address.address = (address.address_line1 or "")[:60]
		customer_address.city = (address.city or "")[:40]
		customer_address.state = (address.state or "")[:40]
		customer_address.zip = (address.pincode or "")[:20]
		customer_address.country = (address.country or "")[:60]


	# record company name when not an individual
	customer_type = frappe.db.get_value("Customer", customer_name, "customer_type")
	if customer_type != "Individual":
		customer_address.company = reference_doc.customer_name

	# Create order information
	order = apicontractsv1.orderType()
	order.invoiceNumber = reference_doc.name

	# build the array of line items
	line_items = apicontractsv1.ArrayOfLineItem()

	for item in reference_doc.get("items"):
		# setup individual line items
		line_item = apicontractsv1.lineItemType()
		line_item.itemId = item.item_code
		line_item.name = item.item_name[:30]
		line_item.description = item.item_name
		line_item.quantity = item.qty
		line_item.unitPrice = cstr(item.rate)

		line_items.lineItem.append(line_item)

	# Adjust duplicate window to avoid duplicate window issues on declines
	duplicateWindowSetting = apicontractsv1.settingType()
	duplicateWindowSetting.settingName = "duplicateWindow"
	# seconds before an identical transaction can be submitted
	duplicateWindowSetting.settingValue = "10"
	settings = apicontractsv1.ArrayOfSetting()
	settings.setting.append(duplicateWindowSetting)

	# Create a transactionRequestType object and add the previous objects to it.
	transaction_request = apicontractsv1.transactionRequestType()
	transaction_request.transactionType = "authCaptureTransaction"
	transaction_request.amount = data.amount
	transaction_request.payment = payment
	transaction_request.order = order
	transaction_request.billTo = customer_address
	transaction_request.lineItems = line_items
	transaction_request.transactionSettings = settings

	# Assemble the complete transaction request
	create_transaction_request = apicontractsv1.createTransactionRequest()
	create_transaction_request.merchantAuthentication = request.merchant_auth
	create_transaction_request.transactionRequest = transaction_request
	create_transaction_request.refId = reference_doc.name

	# Create the controller
	createtransactioncontroller = createTransactionController(create_transaction_request)
	if not frappe.db.get_single_value("Authorizenet Settings", "sandbox_mode"):
		createtransactioncontroller.setenvironment(constants.PRODUCTION)
	createtransactioncontroller.execute()

	return createtransactioncontroller.getresponse()

def to_dict(response):
	response_dict = {}
	if response.getchildren() == []:
		return response.text

	for elem in response.getchildren():
		subdict = to_dict(elem)
		response_dict[re.sub('{.*}', '', elem.tag)] = subdict

	return response_dict
