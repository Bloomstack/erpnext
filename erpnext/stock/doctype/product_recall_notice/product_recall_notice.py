# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.model.document import Document

class ProductRecallNotice(Document):
	pass

@frappe.whitelist()
def create_stock_entry_from_product_recall_notice(product_recall_notice):
	"""
	Create Stock Entry to put items in recall warehouse.

	Args:
		product_recall_notice (doc): Product Recall Notice Doc to create Stock Entry

	Returns:
		stock_entry: returns name of stock entry created with link to its form
	"""
	product_recall_notice = json.loads(product_recall_notice)
	se_items = []
	stock_entry_doc = frappe.new_doc("Stock Entry")

	if product_recall_notice.get("recall_from") == "Warehouse":
		stock_entry_doc.stock_entry_type = "Material Transfer"
	else:
		stock_entry_doc.stock_entry_type = "Material Receipt"

	for item in product_recall_notice.get("items"):
		se_items.append({
			"item_code":item.get("item_code"),
			"qty": item.get("qty"),
			"batch_no": item.get("batch_no"),
			"s_warehouse": item.get("warehouse") if stock_entry_doc.stock_entry_type == "Material Transfer" else None,
			"t_warehouse": product_recall_notice.get("recall_warehouse")
		})
	stock_entry_doc.update({
		"items": se_items
	})
	stock_entry_doc.run_method("set_missing_values")
	stock_entry_doc.save(ignore_permissions=True)

	return {
		"stock_entry": frappe.utils.get_link_to_form('Stock Entry', stock_entry_doc.name)
	}
