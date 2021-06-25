# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import comma_and

class ProductRecall(Document):
	def on_submit(self):
		self.create_product_recall_notice()

	def create_product_recall_notice(self):
		"""
		Create Product Recall Notice with items from the batch entered.
		"""
		batch = frappe.get_doc("Batch", self.batch_no)
		items_in_warehouse = []
		items_delivered = []

		sle_list = frappe.get_list("Stock Ledger Entry",
			[["batch_no", "=", batch.name]], ["name", "voucher_type", "voucher_no"])

		sle_expanded_list = []

		for sle in sle_list:
			sle_doc = frappe.get_doc("Stock Ledger Entry", sle.name).as_dict()

			# append to sle_expanded_list for product recall notice to be created with recall from warehouse
			if sle_doc.voucher_type == "Stock Entry":
				se = frappe.get_doc("Stock Entry", sle_doc.voucher_no).as_dict()
				for item in se.get("items"):
					if item.batch_no:
						sle_data = frappe.get_list("Stock Ledger Entry",
							[["batch_no", "=", item.batch_no]], ["name", "voucher_type", "voucher_no"])
						sle_expanded_list = sle_list + sle_data

			# append to sle_expanded_list for product recall notice to be created with recall from customer
			if sle_doc.voucher_type == "Delivery Note":
				dn = frappe.get_doc("Delivery Note", sle_doc.voucher_no).as_dict()
				for item in dn.get("items"):
					if item.batch_no:
						sle_data = frappe.get_list("Stock Ledger Entry",
							[["batch_no", "=", item.batch_no]], ["name", "voucher_type", "voucher_no"])
						sle_expanded_list = sle_list + sle_data

		# iterate to create product recall notice doc
		for sle_item in sle_expanded_list:
			if sle_item.voucher_type == "Stock Entry":
				se = frappe.get_doc("Stock Entry", sle_item.voucher_no).as_dict()
				for item in se.get("items"):
					if (item.item_code and item.batch_no and item.parent) not in items_in_warehouse and item.batch_no:
						items_in_warehouse = items_in_warehouse + [{
							"item_code": item.item_code,
							"item_name": item.item_name,
							"batch_no": item.batch_no,
							"package_tag": item.package_tag,
							"warehouse": item.t_warehouse,
							"qty": item.qty,
							"reference_doctype": item.parenttype,
							"reference_docname": item.parent
						}]
			if sle_item.voucher_type == "Delivery Note":
				dn = frappe.get_doc("Delivery Note", sle_item.voucher_no).as_dict()
				for item in dn.get("items"):
					if (item.item_code and item.batch_no and item.parent) not in items_delivered and item.batch_no:
						items_delivered = items_delivered + [{
								"customer": dn.customer,
								"item_code": item.item_code,
								"item_name": item.item_name,
								"batch_no": item.batch_no,
								"package_tag": item.package_tag,
								"qty": item.qty,
								"reference_doctype": item.parenttype,
								"reference_docname": item.parent
						}]

		# create list of dictionaries with unique value of item_code and batch_no
		items_in_warehouse = list({(v['item_code'], v['batch_no']): v for v in items_in_warehouse}.values())
		items_delivered = list({(v['item_code'], v['batch_no']): v for v in items_delivered}.values())

		prn_doc_list = []
		if items_delivered:
			# create Product Recall Notice with recall_from Customer
			doc_recall_from_customer = frappe.new_doc("Product Recall Notice")
			doc_recall_from_customer.update({
				"product_recall": self.name,
				"recall_from": "Customer",
				"recall_warehouse": self.recall_warehouse,
				"items": items_delivered
			})
			doc_recall_from_customer.save()
			prn_doc_list.append(doc_recall_from_customer)

		if items_in_warehouse:
			# create Product Recall Notice with recall_from Warehouse
			doc_recall_from_warehouse = frappe.new_doc("Product Recall Notice")
			doc_recall_from_warehouse.update({
				"product_recall": self.name,
				"recall_from": "Warehouse",
				"recall_warehouse": self.recall_warehouse,
				"items": items_in_warehouse
			})
			doc_recall_from_warehouse.save()
			prn_doc_list.append(doc_recall_from_warehouse)

		prn_doc_list = ["""<a href="#Form/Product Recall Notice/{0}">{0}</a>""".format(m.name) for m in prn_doc_list]
		frappe.msgprint(_("{0} created").format(comma_and(prn_doc_list)))
