# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import get_client
from erpnext.erpnext_integrations.taxjar_integration import create_transaction, update_transaction
from frappe.integrations.utils import make_integration_request, update_integration_request

class BackfillTaxJarTransactions(Document):
	def push_transaction(self):
		client = get_client(self)

		if not client:
			return

		TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", self.company,  "tax_account_head")
		SHIP_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", self.company, "shipping_account_head")

		# fetch orders from taxjar for selected date range
		orders = client.list_orders({
			'from_transaction_date': frappe.utils.formatdate(self.from_date, 'yyyy/mm/dd'),
			'to_transaction_date': frappe.utils.formatdate(self.to_date, 'yyyy/mm/dd')
		})
		count = 0
		sucessfull_count = 0
		invoice_orders = frappe.get_all('Sales Invoice',
			filters={"posting_date": ('between', [self.from_date, self.to_date]), "docstatus": "1", "exempt_from_sales_tax": 0, "company": self.company}, 
			fields=[
				'name'
			])
		# fetch all invoice from bloomstack between that date range.
		for doc in invoice_orders:
			# fetch sales tax from invoice which belongs to taxjar configured tax account head
			sales_taxes = frappe.get_all('Sales Taxes and Charges',
				filters={'parenttype': 'Sales Invoice', 'parent': doc.name, 'account_head': TAX_ACCOUNT_HEAD},
				fields=['tax_amount'])
			
			if sales_taxes and sales_taxes[0].tax_amount:
				frappe.publish_realtime('backfill_taxjar_transactions', dict(
					progress = count, heading="Getting tasks", label = 'Pushing backfilled transactions...', total=len(invoice_orders)))

				count = count + 1
				transaction = frappe.enqueue(create_backfill_transaction, doc=doc, orders=orders, client=client, force=self.force, now=True if len(invoice_orders) < 200 else False)
				if transaction:
					sucessfull_count = sucessfull_count + 1
		return {"total_transactions":count, "backfilled_transactions":sucessfull_count}
				
def create_backfill_transaction(doc, orders, client, force=None):
	doc_data = frappe.get_doc("Sales Invoice", doc.name)
	if force:
		if doc.name in orders.data:
			return update_transaction(doc_data, backfill=True)
		else:
			return create_transaction(doc_data, backfill=True)
	else:
		if not doc.name in orders.data:
			return create_transaction(doc_data, backfill=True)