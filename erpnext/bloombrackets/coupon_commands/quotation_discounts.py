import frappe
from frappe.utils import flt, cint
from erpnext.bloombrackets.coupon_commands.utils import flat_item_group_tree_list

NET_TOTAL = "Net Total"
GRAND_TOTAL = "Grand Total"

CMD_SET_DISCOUNT_GRAND_TOTAL_BASIS = "Set Discount Grand Total Basis"
CMD_SET_DISCOUNT_NET_TOTAL_BASIS = "Set Discount Net Total Basis"

CMD_ADD_DISCOUNT = "Add Discount"

CMD_APPLY_DISCOUNT = "Apply Discount"
CMD_APPLY_DISCOUNT_PERCENT = "Apply Discount Percent"
CMD_APPLY_NET_DISCOUNT = "Apply Net Discount"
CMD_APPLY_NET_DISCOUNT_PERCENT = "Apply Net Discount Percent"

CMD_ADD_ITEM_DISCOUNT = "Add Item Discount"
CMD_ADD_ITEM_DISCOUNT_PERCENT = "Add Item Discount Percent"
CMD_ADD_ITEM_DISCOUNT_QTY_MIN = "Add Item Discount Qty Min"
CMD_ADD_ITEM_DISCOUNT_PERCENT_QTY_MIN = "Add Item Discount Percent Qty Min"

CMD_ADD_ITEM_GROUP_DISCOUNT = "Add Item Group Discount"
CMD_ADD_ITEM_GROUP_DISCOUNT_PERCENT = "Add Item Group Discount Percent"
CMD_ADD_ITEM_GROUP_DISCOUNT_QTY_MIN = "Add Item Group Discount Qty Min"
CMD_ADD_ITEM_GROUP_DISCOUNT_PERCENT_QTY_MIN = "Add Item Group Discount Percent Qty Min"

def discount_amount_total_guard(doc):
	"""discount_amount guard to ensure the discount isn't larger than the quotation value"""

	if doc.apply_discount_on == "Net Total":
		if doc.discount_amount > doc.net_total:
			doc.discount_amount = doc.net_total

	else:
		if doc.discount_amount > doc.grand_total:
			doc.discount_amount = doc.grand_total

	if doc.additional_discount_percentage > 100:
		doc.additional_discount_percentage = 100

def set_discount_grand_total_basis(args, ctx):
	"""Sets the quotation apply_discount_of field to "Grand Total".
	
	Parameters:
		args - Unused
		ctx - The script's context
	"""
	doc = ctx["#VARS"]["doc"]
	doc.apply_discount_on = GRAND_TOTAL
	doc.run_method("calculate_taxes_and_totals")

def set_discount_net_total_basis(args, ctx):
	"""Sets the quotation apply_discount_of field to "Net Total".

	Parameters:
		args - Unused
		ctx - The script's context
	"""
	doc = ctx["#VARS"]["doc"]
	doc.apply_discount_on = NET_TOTAL
	doc.run_method("calculate_taxes_and_totals")

	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_SET_DISCOUNT_GRAND_TOTAL_BASIS]
	)

def add_discount(args, ctx):
	"""Sets the quotation discount_amount field.

	Parameters:
		args[0] - The discount value
		ctx - The script's context
	"""
	value = flt(args[0])
	doc = ctx["#VARS"]["doc"]

	doc.discount_amount = (doc.discount_amount or 0) + value
	discount_amount_total_guard(doc)

	doc.additional_discount_percentage = 0
	doc.run_method("calculate_taxes_and_totals")

	# How we undo this script's data
	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_APPLY_DISCOUNT, 0]
	)

def add_item_discount(args, ctx):
	"""Adds a discount value to the existing discount_amount field.

	Parameters:
		args[0] - The item name to match
		args[1] - The discount value
		args[2] - Min item qty to match
		args[3] - Max item qty to match
	"""
	item_name = args[0]
	discount = flt(args[1])
	min_qty = 1 if len(args) < 3 or not args[2] else cint(args[2])
	max_qty = float('inf') if len(args) < 4 or not args[3] or args[3] == 'inf' else cint(args[3])

	doc = ctx["#VARS"]["doc"]
	total_discount = 0
	qty = 0

	for item in doc.items:
		if item.item_code == item_name:
			if qty <= max_qty - min_qty:
				# keep item qty under qty + max_qty
				local_qty = item.qty if item.qty + qty <= max_qty else min(max_qty - qty, item.qty)
				# calculate amount on the available qty
				amount = local_qty * item.rate
				# cap discount_value under amount
				discount_value = discount if discount <= amount else amount
				# track discount amount and qty
				total_discount = total_discount + discount_value
				qty = qty + item.qty
	
	# add discount only on min_qty
	if total_discount > 0 and qty >= min_qty:
		doc.discount_amount = doc.discount_amount + total_discount
		doc.additional_discount_percentage = 0
		discount_amount_total_guard(doc)
		doc.run_method("calculate_taxes_and_totals")

		ctx["#VARS"]["undo_script"].append(
			["CALL", CMD_APPLY_DISCOUNT, 0]
		)

def add_item_group_discount(args, ctx):
	"""Adds a discount value to the existing discount_amount field if an item
	belonging to the provided group is found.

	Parameters:
		args[0] - The item group to match
		args[1] - The discount value
		args[2] - Min item qty to match
		args[3] - Max item qty to match
	"""

	group = args[0]
	discount = flt(args[1])
	min_qty = 1 if len(args) < 3 or not args[2] else cint(args[2])
	max_qty = float('inf') if len(args) < 4 or not args[3] or args[3] == 'inf' else cint(args[3])

	doc = ctx["#VARS"]["doc"]
	total_discount = 0
	qty = 0

	valid_item_groups = flat_item_group_tree_list(group)

	for item in doc.items:
		item_group = frappe.get_value("Item", item.item_code, "item_group")

		if item_group in valid_item_groups:
			if qty <= max_qty - min_qty:
				# keep item qty under qty + max_qty
				local_qty = item.qty if item.qty + qty <= max_qty else min(max_qty - qty, item.qty)
				# calculate amount on the available qty
				amount = local_qty * item.rate
				# cap discount_value under amount
				discount_value = discount if discount <= amount else amount
				# track discount amount and qty
				total_discount = total_discount + discount_value
				qty = qty + item.qty
	
	# add discount only on min_qty
	if total_discount > 0 and qty >= min_qty:
		doc.discount_amount = doc.discount_amount + total_discount
		doc.additional_discount_percentage = 0
		discount_amount_total_guard(doc)
		doc.run_method("calculate_taxes_and_totals")

		ctx["#VARS"]["undo_script"].append(
			["CALL", CMD_APPLY_DISCOUNT, 0]
		)

def add_item_discount_percent(args, ctx):
	"""Adds a discount percentage to the existing discount_amount field per item
	matched to the provided group is found.

	Parameters:
		args[0] - The item group to match
		args[1] - The discount value
		args[2] - Min item qty to match
		args[3] - Max item qty to match
	"""

	doc = ctx["#VARS"]["doc"]
	item_name = args[0]
	percent = flt(args[1])
	min_qty = 1 if len(args) < 3 or not args[2] else cint(args[2])
	max_qty = float('inf') if len(args) < 4 or not args[3] or args[3] == 'inf' else cint(args[3])

	total_discount = 0
	qty = 0

	if percent < 0:
		percent = 0
	if percent > 100:
		percent = 100

	for item in doc.items:

		if item.item_code == item_name:
			if qty <= max_qty - min_qty:
				# keep item qty under qty + max_qty
				local_qty = item.qty if item.qty + qty <= max_qty else min(max_qty - qty, item.qty)
				# calculate amount on the available qty
				amount = local_qty * item.rate
				discount_value = (amount * percent) / 100
				# prevent going negative
				if discount_value > 0:
					# track discount amount and qty
					total_discount = total_discount + discount_value
					qty = qty + item.qty

	if total_discount > 0 and qty > min_qty:
		doc.discount_amount = flt(doc.discount_amount) + total_discount
		doc.additional_discount_percentage = 0
		discount_amount_total_guard(doc)
		doc.run_method("calculate_taxes_and_totals")

		ctx["#VARS"]["undo_script"].append(
			["CALL", CMD_APPLY_DISCOUNT, 0]
		)

def add_item_group_discount_percent(args, ctx):
	"""Adds a discount percentage to the existing discount_amount field if an item
	belonging to the provided group is found.

	Parameters:
		args[0] - The item group to match
		args[1] - The discount value
		args[2] - Min item qty to match
		args[3] - Max item qty to match
	"""

	doc = ctx["#VARS"]["doc"]
	group = args[0]
	percent = flt(args[1])
	min_qty = 1 if len(args) < 3 or not args[2] else cint(args[2])
	max_qty = float('inf') if len(args) < 4 or not args[3] or args[3] == 'inf' else cint(args[3])

	total_discount = 0
	qty = 0

	valid_item_groups = flat_item_group_tree_list(group)

	if percent < 0:
		percent = 0
	if percent > 100:
		percent = 100

	for item in doc.items:
		item_group = frappe.get_value("Item", item.item_code, "item_group")

		if item_group in valid_item_groups:
			if qty <= max_qty:
				# keep item qty under qty + max_qty
				local_qty = item.qty if item.qty + qty <= max_qty else min(max_qty - qty, item.qty)
				# calculate amount on the available qty
				amount = local_qty * item.rate
				discount_value = (amount * percent) / 100
				# prevent going negative
				if discount_value > 0:
					# track discount amount and qty
					total_discount = total_discount + discount_value
					qty = qty + item.qty

	if total_discount > 0 and qty >= min_qty:
		doc.discount_amount = flt(doc.discount_amount) + total_discount
		doc.additional_discount_percentage = 0
		discount_amount_total_guard(doc)
		doc.run_method("calculate_taxes_and_totals")

		ctx["#VARS"]["undo_script"].append(
			["CALL", CMD_APPLY_DISCOUNT, 0]
		)

def apply_discount(args, ctx):
	"""Sets the discount value of the quotation.

	Parameters:
		args[0] - The discount value
	"""

	value = flt(args[0])
	doc = ctx["#VARS"]["doc"]
	doc.discount_amount = value
	doc.additional_discount_percentage = 0
	doc.apply_discount_on = GRAND_TOTAL
	discount_amount_total_guard(doc)
	doc.run_method("calculate_taxes_and_totals")

	# How we undo this script's data
	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_APPLY_DISCOUNT, 0]
	)

def apply_discount_percent(args, ctx):
	"""Sets the discount percent of the quotation.

	Parameters:
		args[0] - The discount percent
	"""

	percent = flt(args[0])
	doc = ctx["#VARS"]["doc"]
	doc.discount_amount = 0
	doc.additional_discount_percentage = percent
	doc.apply_discount_on = GRAND_TOTAL
	discount_amount_total_guard(doc)
	doc.run_method("calculate_taxes_and_totals")

	# How we undo this script's data
	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_APPLY_DISCOUNT, 0]
	)

def apply_net_discount(args, ctx):
	"""Sets the discount value of the quotation and the apply_discount_on to "Net Total"

	Parameters:
		args[0] - The discount value
	"""

	value = flt(args[0])
	doc = ctx["#VARS"]["doc"]
	doc.discount_amount = value
	doc.additional_discount_percentage = 0
	doc.apply_discount_on = NET_TOTAL
	doc.run_method("calculate_taxes_and_totals")

	# How we undo this script's data
	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_APPLY_DISCOUNT, 0]
	)

def apply_net_discount_percent(args, ctx):
	"""Sets the discount percent of the quotation and the apply_discount_on to "Net Total"

	Parameters:
		args[0] - The discount percent
	"""

	percent = flt(args[0])
	doc = ctx["#VARS"]["doc"]
	discount = (doc.net_total * percent) / 100
	doc.discount_amount = 0
	doc.additional_discount_percentage = percent
	doc.apply_discount_on = NET_TOTAL
	doc.run_method("calculate_taxes_and_totals")

	# How we undo this script's data
	ctx["#VARS"]["undo_script"].append(
		["CALL", CMD_APPLY_DISCOUNT, 0]
	)

def load_commands(commands, for_doctype):

	commands.update({
		CMD_SET_DISCOUNT_GRAND_TOTAL_BASIS: set_discount_grand_total_basis,
		CMD_SET_DISCOUNT_NET_TOTAL_BASIS: set_discount_net_total_basis,

		CMD_ADD_DISCOUNT: add_discount,
		CMD_ADD_ITEM_DISCOUNT: add_item_discount,
		CMD_ADD_ITEM_DISCOUNT_PERCENT: add_item_discount_percent,
		CMD_ADD_ITEM_GROUP_DISCOUNT: add_item_group_discount,
		CMD_ADD_ITEM_GROUP_DISCOUNT_PERCENT: add_item_group_discount_percent,

		CMD_APPLY_DISCOUNT: apply_discount,
		CMD_APPLY_DISCOUNT_PERCENT: apply_discount_percent,
		CMD_APPLY_NET_DISCOUNT: apply_discount,
		CMD_APPLY_NET_DISCOUNT_PERCENT: apply_discount_percent,
	})

def load_commands_meta(meta, for_doctype):
	meta.update({
		CMD_SET_DISCOUNT_GRAND_TOTAL_BASIS: {
			"description": "Sets the discount 'Apply On' basis to 'Grand Total'",
			"args": []
		},

		CMD_SET_DISCOUNT_NET_TOTAL_BASIS: {
			"description": "Sets the discount 'Apply On' basis to 'Net Total'",
			"args": []
		},

		CMD_ADD_DISCOUNT: {
			"description": "Adds a discount value to the existing discount in a quotation.",
			"args": [{
				"name": "discount",
				"description": "A discount value",
				"fieldtype": "Currency"
			}]
		},

		CMD_ADD_ITEM_DISCOUNT: {
			"description": "Adds a discount value to the existing discount per matching item.",
			"args": [{
				"name": "item_name",
				"description": "The item name to match",
				"fieldtype": "Link",
				"options": "Item"
			}, {
				"name": "discount",
				"description": "A discount value",
				"fieldtype": "Currency"
			}, {
				"name": "min_qty",
				"description": "The minimum item qty to match",
				"fieldtype": "int"
			}, {
				"name": "max_qty",
				"description": "The maximum item qty to match",
				"fieldtype": "int"
			}]
		},

		CMD_ADD_ITEM_DISCOUNT_PERCENT: {
			"description": "Adds a discount percent to the existing discount per matching item.",
			"args": [{
				"name": "item_name",
				"description": "The item name to match",
				"fieldtype": "Link",
				"options": "Item"
			}, {
				"name": "percent",
				"description": "A discount percent",
				"fieldtype": "Currency"
			}, {
				"name": "min_qty",
				"description": "The minimum item qty to match",
				"fieldtype": "int"
			}, {
				"name": "max_qty",
				"description": "The maximum item qty to match",
				"fieldtype": "int"
			}]
		},
		CMD_ADD_ITEM_GROUP_DISCOUNT: {
			"description": "Adds a discount value to the existing discount per matching item group.",
			"args": [{
				"name": "group_name",
				"description": "The item group name to match",
				"fieldtype": "Link",
				"options": "Item Group"
			}, {
				"name": "discount",
				"description": "A discount value",
				"fieldtype": "Currency"
			}, {
				"name": "min_qty",
				"description": "The minimum item qty to match",
				"fieldtype": "int"
			}, {
				"name": "max_qty",
				"description": "The maximum item qty to match",
				"fieldtype": "int"
			}]
		},

		CMD_ADD_ITEM_GROUP_DISCOUNT_PERCENT: {
			"description": "Adds a discount percent to the existing discount per matching item group.",
			"args": [{
				"name": "group_name",
				"description": "The item group name to match",
				"fieldtype": "Link",
				"options": "Item Group"
			}, {
				"name": "percent",
				"description": "A discount percent",
				"fieldtype": "Currency"
			}, {
				"name": "min_qty",
				"description": "The minimum item qty to match",
				"fieldtype": "int"
			}, {
				"name": "max_qty",
				"description": "The maximum item qty to match",
				"fieldtype": "int"
			}]
		},

		CMD_APPLY_DISCOUNT: {
			"description": "Applies discount value to a quotation based on its grand total.",
			"args": [{
				"name": "discount",
				"description": "A discount value",
				"fieldtype": "Currency"
			}]
		},

		CMD_APPLY_NET_DISCOUNT: {
			"description": "Applies discount value to a quotation based on its net total.",
			"args": [{
				"name": "discount",
				"description": "A discount value",
				"fieldtype": "Currency"
			}]
		},

		CMD_APPLY_DISCOUNT_PERCENT: {
			"description": "Applies discount percentage to a quotation based on its grand total.",
			"args": [{
				"name": "percent",
				"description": "A discount percent value",
				"fieldtype": "float"
			}]
		},

		CMD_APPLY_NET_DISCOUNT_PERCENT: {
			"description": "Applies discount percentage to a quotation based on its net total.",
			"args": [{
				"name": "percent",
				"description": "A discount percent value",
				"fieldtype": "float"
			}]
		}
	})

