# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import json

from six import string_types

import frappe
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from frappe.utils import cint, nowdate
from frappe.utils.nestedset import get_root_of


@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, search_value="", pos_profile=None):
	data = dict()
	warehouse = ""
	display_items_in_stock = 0

	if pos_profile:
		warehouse, display_items_in_stock = frappe.db.get_value('POS Profile', pos_profile, ['warehouse', 'display_items_in_stock'])

	if not frappe.db.exists('Item Group', item_group):
		item_group = get_root_of('Item Group')

	if search_value:
		data = search_serial_or_batch_or_barcode_number(search_value)

	item_code = data.get("item_code") if data.get("item_code") else search_value
	serial_no = data.get("serial_no") if data.get("serial_no") else ""
	batch_no = data.get("batch_no") if data.get("batch_no") else ""
	barcode = data.get("barcode") if data.get("barcode") else ""

	condition = get_conditions(item_code, serial_no, batch_no, barcode)

	if pos_profile:
		condition += get_item_group_condition(pos_profile)

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])
	# locate function is used to sort by closest match from the beginning of the value


	result = []

	items_data = frappe.db.sql(""" SELECT name as item_code,
			item_name, image as item_image, idx as idx,is_stock_item
		FROM
			`tabItem`
		WHERE
			disabled = 0 and has_variants = 0 and is_sales_item = 1
			and item_group in (select name from `tabItem Group` where lft >= {lft} and rgt <= {rgt})
			and {condition} order by idx desc limit {start}, {page_length}"""
		.format(
			start=start, page_length=page_length,
			lft=lft, rgt=rgt,
			condition=condition
		), as_dict=1)

	if items_data:
		items = [d.item_code for d in items_data]
		item_prices_data = frappe.get_all("Item Price",
			fields = ["item_code", "price_list_rate", "currency"],
			filters = {'price_list': price_list, 'item_code': ['in', items]})

		item_prices, bin_data = {}, {}
		for d in item_prices_data:
			item_prices[d.item_code] = d


		if display_items_in_stock:
			filters = {'actual_qty': [">", 0], 'item_code': ['in', items]}

			if warehouse:
				filters['warehouse'] = warehouse

			bin_data = frappe.get_all("Bin", fields = ["item_code", "sum(actual_qty) as actual_qty"],
			filters = filters, group_by = "item_code")
			# next line stores item_code as key and actual_qty as value pair for all items
			bin_item={bin_item.item_code: bin_item.actual_qty for bin_item in bin_data}
			
		for item in items_data:
			row = {}
			# next line fetches the value(actual_qty) using asked item_code as key
			actual_qty= bin_item.get(item.item_code)
			if display_items_in_stock and actual_qty: #checks for display_items_in_stock set to 1 and actual_qty eixists
				row.update(item)
				item_price = item_prices.get(item.item_code) or {}
				row.update({
					'price_list_rate': item_price.get('price_list_rate'),
					'currency': item_price.get('currency'),
					'actual_qty': actual_qty
				})
				result.append(row)
			# REDUCE IN LENGTH OF TOTAL NUMBER OF ITEM DISPLAY (PREVIOUS LENGTH WAS 40)
			# REQUIRES ELSE PART IN CASE OF display_items_in_stock IS SET TO 0

	res = {
		'items': result
	}

	if serial_no:
		res.update({
			'serial_no': serial_no
		})

	if batch_no:
		res.update({
			'batch_no': batch_no
		})

	if barcode:
		res.update({
			'barcode': barcode
		})

	return res

@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value):
	# search barcode no
	barcode = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
	if barcode:
		return barcode

	# search serial no
	serial_no = frappe.get_all('Serial No',
		{"name": search_value, "warranty_expiry_date": ["<=", nowdate()], "amc_expiry_date": ["<=", nowdate()]},
		['name as serial_no', 'item_code'])
	if serial_no:
		return serial_no[0]

	# search batch no
	batch_no = frappe.get_all('Batch',
		{"name": search_value, "batch_qty": [">", 0], "disabled": 0, "expiry_date": ["<=", nowdate()]},
		['name as batch_no', 'item as item_code'])
	if batch_no:
		return batch_no[0]

	return {}

def get_conditions(item_code, serial_no, batch_no, barcode):
	if serial_no or batch_no or barcode:
		return "name = {0}".format(frappe.db.escape(item_code))

	return """(name like {item_code}
		or item_name like {item_code})""".format(item_code = frappe.db.escape('%' + item_code + '%'))

def get_item_group_condition(pos_profile):
	cond = "and 1=1"
	item_groups = get_item_groups(pos_profile)
	if item_groups:
		cond = "and item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

	return cond % tuple(item_groups)

def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = []
	cond = "1=1"
	pos_profile= filters.get('pos_profile')

	if pos_profile:
		item_groups = get_item_groups(pos_profile)

		if item_groups:
			cond = "name in (%s)"%(', '.join(['%s']*len(item_groups)))
			cond = cond % tuple(item_groups)

	return frappe.db.sql(""" select distinct name from `tabItem Group`
			where {condition} and (name like %(txt)s) limit {start}, {page_len}"""
		.format(condition = cond, start=start, page_len= page_len),
			{'txt': '%%%s%%' % txt})
