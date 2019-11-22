# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.model.document import Document
from frappe.utils import cint, flt


class PackingSlip(Document):

	def validate(self):
		"""
			* Check if packing cases do not overlap
			* Check if packed quantities doesn't exceed ordered quantities
		"""

		self.validate_case_nos()
		self.validate_qty()

		from erpnext.utilities.transaction_base import validate_uom_is_integer
		validate_uom_is_integer(self, "stock_uom", "qty")
		validate_uom_is_integer(self, "weight_uom", "net_weight")

	def on_submit(self):
		self.create_delivery_note()

	def validate_case_nos(self):
		"""
			Validate if case numbers overlap. If they do, recommend next case no.
		"""

		if not self.from_case_no:
			frappe.throw(_("Please specify a valid 'From Package No.'"))
		elif not self.to_case_no:
			self.to_case_no = self.from_case_no
		elif self.from_case_no > self.to_case_no:
			frappe.throw(_("'To Package No.' cannot be less than 'From Package No.'"))

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

	def validate_qty(self):
		"""
			Check packed quantity across Packing Slips and Sales Order, and throw
			validation if packed quantity is greater than ordered quantity.
		"""

		# Get Sales Order Items, Item Quantity Dict and No. of Cases for this Packing slip
		so_details, ps_item_qty, no_of_cases = self.get_details_for_packing()

		for item in so_details:
			new_packed_qty = (flt(ps_item_qty[item.item_code]) * no_of_cases) + flt(item.packed_qty)
			if new_packed_qty > flt(item.qty) and no_of_cases:
				item.recommended_qty = (flt(item.qty) - flt(item.packed_qty)) / (no_of_cases or 1)
				item.specified_qty = flt(ps_item_qty[item.item_code])
				if not item.packed_qty: item.packed_qty = 0

				frappe.throw(_("Quantity for Item {0} must be less than {1}").format(item.item_code, item.recommended_qty))

	def create_delivery_note(self):
		# TODO: create delivery note and set serial and batch details
		pass

		# so = frappe.get_doc("Sales Order", self.sales_order)
		# so_items = {item.item_code: item.name for item in so.items}

		# for packing_item in self.items:
		# 	if packing_item.item_code in so_items:
		# 		for row in so.items:
		# 			if row.name == so_items.get(packing_item.item_code):
		# 				frappe.db.set_value("Sales Order Item", row.name, "serial_no", packing_item.serial_no)

	def get_details_for_packing(self):
		"""
			Returns
			* 'Sales Order Items' query result as a list of dict
			* Item Quantity dict of current packing slip doc
			* No. of Cases of this packing slip
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
		res = frappe.db.sql("""
			SELECT
				soi.item_code,
				SUM(soi.qty) AS qty,
				(
					SELECT
						SUM(psi.qty * (ABS(ps.to_case_no - ps.from_case_no) + 1))
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

		ps_item_qty = {item.item_code: item.qty for item in self.items}
		no_of_cases = cint(self.to_case_no) - cint(self.from_case_no) + 1

		return res, ps_item_qty, no_of_cases

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

		so_details, ps_item_qty, no_of_cases = self.get_details_for_packing()
		for item in so_details:
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


def item_details(doctype, txt, searchfield, start, page_len, filters):
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
