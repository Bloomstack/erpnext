# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

from six import text_type

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, flt, get_link_to_form
from frappe.utils.data import add_days
from frappe.utils.jinja import render_template

class UnableToSelectBatchError(frappe.ValidationError):
	pass


def get_name_from_hash():
	"""
	Get a name for a Batch by generating a unique hash.
	:return: The hash that was generated.
	"""
	temp = None
	while not temp:
		temp = frappe.generate_hash()[:7].upper()
		if frappe.db.exists('Batch', temp):
			temp = None

	return temp


def batch_uses_naming_series():
	"""
	Verify if the Batch is to be named using a naming series
	:return: bool
	"""
	use_naming_series = cint(frappe.db.get_single_value('Stock Settings', 'use_naming_series'))
	return bool(use_naming_series)


def _get_batch_prefix():
	"""
	Get the naming series prefix set in Stock Settings.

	It does not do any sanity checks so make sure to use it after checking if the Batch
	is set to use naming series.
	:return: The naming series.
	"""
	naming_series_prefix = frappe.db.get_single_value('Stock Settings', 'naming_series_prefix')
	if not naming_series_prefix:
		naming_series_prefix = 'BATCH-'

	return naming_series_prefix


def _make_naming_series_key(prefix):
	"""
	Make naming series key for a Batch.

	Naming series key is in the format [prefix].[#####]
	:param prefix: Naming series prefix gotten from Stock Settings
	:return: The derived key. If no prefix is given, an empty string is returned
	"""
	if not text_type(prefix):
		return ''
	else:
		return prefix.upper() + '.#####'


def get_batch_naming_series():
	"""
	Get naming series key for a Batch.

	Naming series key is in the format [prefix].[#####]
	:return: The naming series or empty string if not available
	"""
	series = ''
	if batch_uses_naming_series():
		prefix = _get_batch_prefix()
		key = _make_naming_series_key(prefix)
		series = key

	return series


class Batch(Document):
	def autoname(self):
		"""Generate random ID for batch if not specified"""
		if not self.batch_id:
			create_new_batch, batch_number_series = frappe.db.get_value('Item', self.item,
				['create_new_batch', 'batch_number_series'])

			if create_new_batch:
				if batch_number_series:
					self.batch_id = make_autoname(batch_number_series)
				elif batch_uses_naming_series():
					self.batch_id = self.get_name_from_naming_series()
				else:
					self.batch_id = get_name_from_hash()
			else:
				frappe.throw(_('Batch ID is mandatory'), frappe.MandatoryError)

		self.name = self.batch_id

	def onload(self):
		self.image = frappe.db.get_value('Item', self.item, 'image')

	def validate(self):
		self.item_has_batch_enabled()
		self.calculate_batch_qty()
		self.validate_display_on_website()

	def item_has_batch_enabled(self):
		if frappe.db.get_value("Item", self.item, "has_batch_no") == 0:
			frappe.throw(_("The selected item cannot have Batch"))

	def calculate_batch_qty(self):
		self.batch_qty = frappe.db.get_value("Stock Ledger Entry", {"docstatus": 1, "batch_no": self.name}, "sum(actual_qty)")

	def before_save(self):
		has_expiry_date, shelf_life_in_days = frappe.db.get_value('Item', self.item, ['has_expiry_date', 'shelf_life_in_days'])
		if not self.expiry_date and has_expiry_date and shelf_life_in_days:
			self.expiry_date = add_days(self.manufacturing_date, shelf_life_in_days)

		if has_expiry_date and not self.expiry_date:
			frappe.throw(msg=_("Please set {0} for Batched Item {1}, which is used to set {2} on Submit.") \
				.format(frappe.bold("Shelf Life in Days"),
					get_link_to_form("Item", self.item),
					frappe.bold("Batch Expiry Date")),
				title=_("Expiry Date Mandatory"))

	def get_name_from_naming_series(self):
		"""
		Get a name generated for a Batch from the Batch's naming series.
		:return: The string that was generated.
		"""
		naming_series_prefix = _get_batch_prefix()
		# validate_template(naming_series_prefix)
		naming_series_prefix = render_template(str(naming_series_prefix), self.__dict__)
		key = _make_naming_series_key(naming_series_prefix)
		name = make_autoname(key)

		return name

	def validate_display_on_website(self):
		"""
		Uncheck website display status from all other batches for the current batch's item
		"""

		batches = frappe.get_all('Batch', filters={'item': self.item, 'name': ['!=', self.name]})

		for batch in batches:
			frappe.db.set_value('Batch', batch, 'display_on_website', False)


@frappe.whitelist()
def get_batch_qty(batch_no=None, warehouse=None, item_code=None):
	"""Returns batch actual qty if warehouse is passed,
		or returns dict of qty by warehouse if warehouse is None

	The user must pass either batch_no or batch_no + warehouse or item_code + warehouse

	:param batch_no: Optional - give qty for this batch no
	:param warehouse: Optional - give qty for this warehouse
	:param item_code: Optional - give qty for this item"""

	out = 0
	if batch_no and warehouse:
		out = float(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where warehouse=%s and batch_no=%s""",
			(warehouse, batch_no))[0][0] or 0)

	if batch_no and not warehouse:
		out = frappe.db.sql('''select warehouse, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where batch_no=%s
			group by warehouse''', batch_no, as_dict=1)

	if not batch_no and item_code and warehouse:
		out = frappe.db.sql('''select batch_no, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where item_code = %s and warehouse=%s
			group by batch_no''', (item_code, warehouse), as_dict=1)

	return out


@frappe.whitelist()
def get_batches_by_oldest(item_code, warehouse):
	"""Returns the oldest batch and qty for the given item_code and warehouse"""
	batches = get_batch_qty(item_code=item_code, warehouse=warehouse)
	batches_dates = [[batch, frappe.get_value('Batch', batch.batch_no, 'expiry_date')] for batch in batches]
	batches_dates.sort(key=lambda tup: tup[1])
	return batches_dates


@frappe.whitelist()
def split_batch(batch_no, item_code, warehouse, qty, new_batch_id=None):
	"""Split the batch into a new batch"""
	batch = frappe.get_doc(dict(doctype='Batch', item=item_code, batch_id=new_batch_id)).insert()

	company = frappe.db.get_value('Stock Ledger Entry', dict(
			item_code=item_code,
			batch_no=batch_no,
			warehouse=warehouse
		), ['company'])

	stock_entry = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Repack',
		company=company,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=warehouse,
				batch_no=batch_no
			),
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				t_warehouse=warehouse,
				batch_no=batch.name
			),
		]
	))
	stock_entry.set_stock_entry_type()
	stock_entry.insert()
	stock_entry.submit()

	return batch.name


def set_batch_nos(doc, warehouse_field, throw=False):
	"""Automatically select `batch_no` for outgoing items in item table"""
	for d in doc.items:
		qty = d.get('stock_qty') or d.get('transfer_qty') or d.get('qty') or 0
		has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')
		warehouse = d.get(warehouse_field, None)
		if has_batch_no and warehouse and qty > 0:
			if not d.batch_no:
				d.batch_no = get_batch_no(d.item_code, warehouse, qty, throw, d.serial_no)
			else:
				batch_qty = get_batch_qty(batch_no=d.batch_no, warehouse=warehouse)
				if flt(batch_qty, d.precision("qty")) < flt(qty, d.precision("qty")):
					frappe.throw(_("Row #{0}: The batch {1} has only {2} qty. Please select another batch which has {3} qty available or split the row into multiple rows, to deliver/issue from multiple batches").format(d.idx, d.batch_no, batch_qty, qty))

@frappe.whitelist()
def get_batch_no(item_code, warehouse, qty=1, throw=False, serial_no=None):
	"""
	Get batch number using First Expiring First Out method.
	:param item_code: `item_code` of Item Document
	:param warehouse: name of Warehouse to check
	:param qty: quantity of Items
	:return: String represent batch number of batch with sufficient quantity else an empty String
	"""

	batch_no = None
	batches = get_batches(item_code, warehouse, qty, throw, serial_no)

	for batch in batches:
		if cint(qty) <= cint(batch.qty):
			batch_no = batch.batch_id
			break

	if not batch_no:
		frappe.msgprint(_('Please select a Batch for Item {0}. Unable to find a single batch that fulfills this requirement').format(frappe.bold(item_code)))
		if throw:
			raise UnableToSelectBatchError

	return batch_no


def get_batches(item_code, warehouse, qty=1, throw=False, serial_no=None, as_dict=True):
	from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
	cond = ''
	if serial_no and frappe.get_cached_value('Item', item_code, 'has_batch_no'):
		serial_nos = get_serial_nos(serial_no)
		batch = frappe.get_all("Serial No",
			fields = ["distinct batch_no"],
			filters= {
				"item_code": item_code,
				"warehouse": warehouse,
				"name": ("in", serial_nos)
			}
		)

		if not batch:
			validate_serial_no_with_batch(serial_nos, item_code)

		if batch and len(batch) > 1:
			return []

		cond = " and batch.name = %s" % (frappe.db.escape(batch[0].batch_no))

	batches = frappe.db.sql("""
		SELECT
			batch.batch_id,
			sum(sle.actual_qty) AS qty
		FROM
			`tabBatch` AS batch
				JOIN `tabStock Ledger Entry` AS sle ignore index (item_code, warehouse)
					ON (batch.batch_id = sle.batch_no)
		WHERE
			sle.item_code = %s
				AND sle.warehouse = %s
				AND batch.disabled = 0
				AND (batch.expiry_date >= CURDATE() or batch.expiry_date IS NULL)
				{0}
		GROUP BY
			batch.batch_id
		HAVING
			sum(sle.actual_qty) >= %s
		ORDER BY
			batch.expiry_date ASC,
			batch.creation ASC
		""".format(cond),
		(item_code, warehouse, qty),
		as_dict=as_dict
	)

	return batches


def validate_serial_no_with_batch(serial_nos, item_code):
	if frappe.get_cached_value("Serial No", serial_nos[0], "item_code") != item_code:
		frappe.throw(_("The serial no {0} does not belong to item {1}")
			.format(get_link_to_form("Serial No", serial_nos[0]), get_link_to_form("Item", item_code)))

	serial_no_link = ','.join([get_link_to_form("Serial No", sn) for sn in serial_nos])

	message = "Serial Nos" if len(serial_nos) > 1 else "Serial No"
	frappe.throw(_("There is no batch found against the {0}: {1}")
		.format(message, serial_no_link))


@frappe.whitelist()
def update_batch_doc(batch_no, qi_name, item_code):
	batch_data = get_batch_fields(batch_no) or frappe._dict()
	quality_data = get_qi_fields(qi_name) or frappe._dict()
	compliance_data = get_ci_fields(item_code) or frappe._dict()
	readings_data = get_readings_for_qi(qi_name) or frappe._dict()

	frappe.db.set_value("Batch", batch_no, {
		"thc": quality_data.thc,
		"cbd": quality_data.cbd,
		"label_details": frappe.render_template(
			"templates/includes/label_order_material_request.html", dict(
				quality_data=quality_data,
				compliance_data=compliance_data,
				readings_data=readings_data,
				batch_data=batch_data)
		)
	})


def get_batch_fields(batch_no):
	return frappe.db.get_value("Batch", batch_no, [
		"manufacturing_date",
		"harvest_date",
		"packaged_date",
	], as_dict=1)


def get_qi_fields(qi_name):
	return frappe.db.get_value("Quality Inspection", qi_name, [
		"thc",
		"cbd",
		"testing_lab",
		"testing_result_link",
		"package_tag",
		"testing_date",
		"manufacturer_name",
		"manufacturer_website",
		"qty",
		"uom",
		"strain_notes",
		"verified_by",
	], as_dict=1)


def get_ci_fields(item_code):
	return frappe.db.get_value("Item", item_code, "strain_type", as_dict=1)


def get_readings_for_qi(qi_name):
	readings = frappe.get_all("Quality Inspection Reading",
		filters={"parent": qi_name}, fields=["specification", "reading_1"])
	readings_info = {reading.specification: reading.reading_1 for reading in readings}
	return readings_info


@frappe.whitelist(allow_guest=True)
def get_active_batch(item_code):
	"""
	Get the current active batch for the given item

	Args:
		item_code (str): The item code

	Returns:
		dict: The details for the active Batch
			Example: {
				"name": "TEST-ITEM-CODE",
				"item": "TEST-ITEM-CODE",
				"item_name": "Test Item",
				"stock_uom": "Unit",
				"thc": 10.0,
				"cbd": 10.0,
				"certificate_of_analysis": "/files/coa.pdf"
			}
	"""
	fields = ["name", "item", "item_name", "stock_uom", "thc", "cbd", "certificate_of_analysis", "batch_qty"]
	active_batch = frappe.get_all("Batch", filters={"item": item_code, "display_on_website": 1}, fields=fields, limit=1)
	if active_batch:
		from erpnext.stock.stock_balance import get_reserved_qty
		active_batch = active_batch[0]
		warehouse = frappe.db.get_value("Stock Ledger Entry", {'batch_no': active_batch.get("name")}, ['warehouse'])
		batch_reserved_qty = get_reserved_qty(active_batch.get("item"), warehouse, active_batch.get("name"))
		active_batch['batch_reserved_qty'] = active_batch['batch_qty'] - batch_reserved_qty
	else:
		active_batch = {}
	return active_batch

@frappe.whitelist()
def create_coa_material_request(source_name, target_doc=None):
	"""
	Creating Material Request from Batch.

	Args:
		source_name (string): batch name
		target_doc (json, optional): json of new material_request doc. Defaults to None.

	Returns:
		target_doc (json): new material_request doc
	"""
	doc = frappe.get_doc("Batch", source_name)
	target_doc = frappe.new_doc("Material Request")
	return target_doc
