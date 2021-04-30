# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class WasteDisposal(Document):

	def before_submit(self):
		self.stock_entry = create_stock_entry_for_waste_disposal(self)


@frappe.whitelist()
def create_stock_entry_for_waste_disposal(doc):
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	stock_entry = get_mapped_doc("Waste Disposal", doc.name, {
		"Waste Disposal": {
			"doctype": "Stock Entry",
			"company": "company"
		},
		"Waste Disposal Item": {
			"doctype": "Stock Entry Detail",
			"field_map": {
				"package_tag": "package_tag",
				"warehouse": "s_warehouse",
				"batch_no": "batch_no",
				"serial_no": "serial_no"
			}
		}
	})

	stock_entry.stock_entry_type = "Material Issue"
	stock_entry.save()
	stock_entry.submit()

	return stock_entry.name


@frappe.whitelist()
def get_items(warehouse, posting_date, posting_time, company):
	lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])

	items = frappe.db.sql("""
		SELECT
			i.name AS item_code,
			i.item_name AS item_name,
			bin.warehouse AS warehouse
		FROM
			tabBin bin
				JOIN tabItem i ON i.name = bin.item_code
		WHERE
			i.disabled = 0
				AND EXISTS(
					SELECT
						name
					FROM
						`tabWarehouse`
					WHERE
						lft >= %s
							AND rgt <= %s
							AND name = bin.warehouse
				)
	""", (lft, rgt), as_dict=True)

	items += frappe.db.sql("""
		SELECT
			i.name AS item_code,
			i.item_name AS item_name,
			id.default_warehouse AS warehouse
		FROM
			tabItem i
				JOIN `tabItem Default` id ON i.name = id.parent
		WHERE
			i.is_stock_item = 1
				AND i.has_serial_no = 0
				AND i.has_batch_no = 0
				AND i.has_variants = 0
				AND i.disabled = 0
				AND id.company = %s
				AND EXISTS(
					SELECT
						name
					FROM
						`tabWarehouse`
					WHERE
						lft >= %s
							AND rgt <= %s
							AND name = id.default_warehouse
				)
		GROUP BY
			i.name
	""", (lft, rgt, company), as_dict=True)

	res = []

	for item in items:
		item_details = get_batch_and_qty_and_package_tag(warehouse=item.warehouse, item_code=item.item_code) or []

		for item_detail in item_details:
			if item_detail.qty > 0:
				res.append({
					"item_code": item.item_code,
					"warehouse": item.warehouse,
					"package_tag": item_detail.package_tag,
					"qty": item_detail.qty,
					"item_name": item.item_name,
					"current_qty": item_detail.qty,
					"batch_no": item_detail.batch_no
				})

	return res

def get_batch_and_qty_and_package_tag(warehouse, item_code):
	"""Returns batch, actual qty and package tag

	:param warehouse: Optional - give qty for this warehouse
	:param item_code: Optional - give qty for this item"""

	return frappe.db.sql('''select batch_no, package_tag, sum(actual_qty) as qty
		from `tabStock Ledger Entry`
		where item_code = %s and warehouse=%s
		group by batch_no''', (item_code, warehouse), as_dict=True)
