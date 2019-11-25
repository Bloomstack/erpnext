# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt


class PackingSlip(Document):
	def validate(self):
		"""
			* Check if packing cases do not overlap
			* Check for duplicate and zero-quantity items
			* Check if packed quantities doesn't exceed ordered quantities
			* If all checks pass, calculate net weights from package items
		"""

		self.validate_case_nos()
		self.validate_item_details()
		self.validate_packed_qty()
		self.calculate_package_weights()

	def on_submit(self):
		self.create_delivery_note()

	def validate_case_nos(self):
		"""
			Validate if case numbers overlap. If they do, recommend next case no.
		"""

		# check for empty and invalid case numbers
		if not self.to_case_no:
			self.to_case_no = self.from_case_no
		elif self.from_case_no > self.to_case_no:
			frappe.throw(_("Final package number should be greater than the starting package number"))

		# check for already used case numbers
		res = frappe.db.sql("""
			SELECT
				name
			FROM
				`tabPacking Slip`
			WHERE
				sales_order = %(sales_order)s
					AND docstatus = 1
					AND ((from_case_no BETWEEN %(from_case_no)s AND %(to_case_no)s)
						OR (to_case_no BETWEEN %(from_case_no)s AND %(to_case_no)s)
						OR (%(from_case_no)s BETWEEN from_case_no AND to_case_no))
			""", {
				"sales_order": self.sales_order,
				"from_case_no": self.from_case_no,
				"to_case_no": self.to_case_no
			})

		if res:
			frappe.throw(_("The provided case numbers are already in use. Try case number {0} and above").format(self.get_recommended_case_no()))

	def validate_item_details(self):
		# validate non-positive item quantities
		for item in self.items:
			if item.qty <= 0:
				frappe.throw(_("Row {0}: Quantity of item {1} should be greater than 0.".format(item.idx, item.item_code)))

		# validate duplicate items
		items = list(set([item.item_code for item in self.items]))
		if len(items) != len(self.items):
			frappe.throw(_("You have entered duplicate items. Please rectify and try again."))

	def validate_packed_qty(self):
		"""
			Check packed quantity across Packing Slips and Sales Order, and throw
			validation if packed quantity is lesser or greater than ordered quantity.
		"""

		so_items = self.get_ordered_items()
		ps_items = {item.item_code: item.qty for item in self.items}

		for so_item in so_items:
			previous_packed_qty = flt(so_item.packed_qty)
			current_packed_qty = flt(ps_items.get(so_item.item_code))
			total_packed_qty = current_packed_qty + previous_packed_qty

			if total_packed_qty > flt(so_item.qty):
				so_item.recommended_qty = (flt(so_item.qty) - previous_packed_qty)
				frappe.throw(_("Quantity for item {0} must be less than {1}").format(so_item.item_code, so_item.recommended_qty))

	def calculate_package_weights(self):
		from erpnext.utilities.transaction_base import validate_uom_is_integer
		validate_uom_is_integer(self, "stock_uom", "qty")
		validate_uom_is_integer(self, "weight_uom", "net_weight")

		# validate for unequal item weight UOMs
		item_weight_uoms = list(set([item.weight_uom for item in self.items if item.weight_uom]))
		if not item_weight_uoms:
			frappe.throw(_("Please set a weight UOM for the items to calculate package weights."))

		if len(item_weight_uoms) > 1:
			frappe.throw(_("Different item UOMs will lead to incorrect net weight value. Make sure that each item's net weight is in the same UOM."))

		self.net_weight_uom = self.gross_weight_uom = item_weight_uoms[0]

		# set net and gross package weight
		net_weight = sum([flt(item.net_weight) * flt(item.qty) for item in self.items])
		self.net_weight_pkg = round(net_weight, 2)

		if not flt(self.gross_weight_pkg):
			self.gross_weight_pkg = self.net_weight_pkg

	def create_delivery_note(self):
		delivery_note = make_delivery_note(self.name)
		delivery_note.insert()
		frappe.msgprint(_("Delivery note {0} created".format(delivery_note.name)))
		return delivery_note.name

	def get_ordered_items(self):
		"""
			Returns details on ordered and already packed items
		"""

		# also pick custom fields from Sales Order
		custom_fields = ', '.join(['soi.`{0}`'.format(d.fieldname)
			for d in frappe.get_meta("Sales Order Item").get_custom_fields()
			if d.fieldtype not in no_value_fields])

		if custom_fields:
			custom_fields = ', ' + custom_fields

		condition = ""
		items = list(set([item.item_code for item in self.items]))
		if items:
			condition = " and soi.item_code in (%s)" % (", ".join(["%s"] * len(items)))

		# gets item code, qty per item code, latest packed qty per item code and stock uom
		so_items = frappe.db.sql("""
			SELECT
				soi.item_code,
				SUM(soi.qty) AS qty,
				(
					SELECT
						SUM(psi.qty)
					FROM
						`tabPacking Slip` AS ps,
						`tabPacking Slip Item` AS psi
					WHERE
						ps.name = psi.parent
							AND ps.docstatus = 1
							AND ps.sales_order = soi.parent
							AND psi.item_code = soi.item_code
				) AS packed_qty,
				soi.stock_uom,
				soi.item_name,
				soi.description
				{custom_fields}
			FROM
				`tabSales Order Item` AS soi
			WHERE
				soi.parent = %s
				{condition}
			GROUP BY
				soi.item_code
			""".format(condition=condition, custom_fields=custom_fields), tuple([self.sales_order] + items), as_dict=1)

		return so_items

	def update_item_details(self):
		"""
			Fill empty columns in Packing Slip Item
		"""

		if not self.from_case_no:
			self.from_case_no = self.get_recommended_case_no()

		for item in self.items:
			item.update(frappe.db.get_value("Item", item.item_code, ["weight_per_unit", "weight_uom"], as_dict=True))

	def get_recommended_case_no(self):
		"""
			Returns the next case number for a new Packing Slip
		"""

		recommended_case_no = frappe.db.get_value("Packing Slip",
			{"sales_order": self.sales_order, "docstatus": 1}, "MAX(to_case_no)")

		return cint(recommended_case_no) + 1

	def get_items(self):
		self.set("items", [])

		custom_fields = frappe.get_meta("Sales Order Item").get_custom_fields()

		so_items = self.get_ordered_items()
		for item in so_items:
			if flt(item.qty) > flt(item.packed_qty):
				ch = self.append('items', {})
				ch.item_code = item.item_code
				ch.item_name = item.item_name
				ch.stock_uom = item.stock_uom
				ch.description = item.description
				ch.qty = flt(item.qty) - flt(item.packed_qty)

				# copy custom fields
				for d in custom_fields:
					if item.get(d.fieldname):
						ch.set(d.fieldname, item.get(d.fieldname))

		self.update_item_details()


def get_item_details(doctype, txt, searchfield, start, page_len, filters):
	if not filters:
		filters = {}

	item_details = []
	if filters.get("sales_order"):
		items = frappe.get_all("Sales Order Item",
			filters={"parent": filters.get("sales_order")},
			fields=["distinct(item_code)"])
		items = [item.item_code for item in items]

		item_details = frappe.get_all("Item",
			filters={"item_code": ["IN", items],
				frappe.db.escape(searchfield): ["LIKE", "{0}".format("%%%s%%" % frappe.db.escape(txt))]},
			fields=["name", "item_name", "description"],
			limit=page_len,
			as_list=True)

	return item_details


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.customer = frappe.db.get_value("Sales Order", source.sales_order, "customer")

	def update_item(source, target, source_parent):
		target.against_sales_order = source_parent.sales_order

	doclist = get_mapped_doc("Packing Slip", source_name, {
		"Packing Slip": {
			"doctype": "Delivery Note"
		},
		"Packing Slip Item": {
			"doctype": "Delivery Note Item",
			"field_map": {
				"source_warehouse": "warehouse",
				"stock_uom": "uom"
			},
			"postprocess": update_item
		},
	}, target_doc, set_missing_values)

	return doclist
