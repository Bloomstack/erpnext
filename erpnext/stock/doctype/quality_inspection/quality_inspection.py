# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from erpnext.stock.doctype.batch.batch import update_batch_doc
from erpnext.stock.doctype.quality_inspection_template.quality_inspection_template import get_template_details
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class QualityInspection(Document):
	def validate(self):
		if not self.readings and self.item_code:
			self.get_item_specification_details()

		if self.reference_type in ["Purchase Invoice", "Purchase Receipt"] and self.reference_name:
			self.get_purchase_item_details()

	def get_item_specification_details(self):
		if not self.quality_inspection_template:
			self.quality_inspection_template = frappe.db.get_value('Item',
				self.item_code, 'quality_inspection_template')

		if not self.quality_inspection_template: return

		self.set('readings', [])
		parameters = get_template_details(self.quality_inspection_template)
		for d in parameters:
			child = self.append('readings', {})
			child.specification = d.specification
			child.value = d.value
			child.status = "Accepted"

	def validate_certificate_of_analysis(self):
		compliance_item = frappe.db.exists("Compliance Item", self.item_code)
		if compliance_item and self.inspection_by == "External" and not self.certificate_of_analysis:
			frappe.throw(_("Please attach a Certificate of Analysis"))

	def get_quality_inspection_template(self):
		template = ''
		if self.bom_no:
			template = frappe.db.get_value('BOM', self.bom_no, 'quality_inspection_template')

		if not template:
			template = frappe.db.get_value('BOM', self.item_code, 'quality_inspection_template')

		self.quality_inspection_template = template
		self.get_item_specification_details()

	def before_submit(self):
		self.validate_certificate_of_analysis()

	def on_submit(self):
		self.update_qc_reference()
		if self.batch_no:
			self.set_batch_coa()
		if self.thc or self.cbd:
			update_batch_doc(self.batch_no, self.name, self.item_code)

	def on_cancel(self):
		self.update_qc_reference()

	def update_qc_reference(self):
		quality_inspection = self.name if self.docstatus == 1 else ""
		doctype = self.reference_type + ' Item'
		if self.reference_type == 'Stock Entry':
			doctype = 'Stock Entry Detail'

		if self.reference_type and self.reference_name:
			frappe.db.sql("""update `tab{child_doc}` t1, `tab{parent_doc}` t2
				set t1.quality_inspection = %s, t2.modified = %s
				where t1.parent = %s and t1.item_code = %s and t1.parent = t2.name"""
				.format(parent_doc=self.reference_type, child_doc=doctype),
				(quality_inspection, self.modified, self.reference_name, self.item_code))

	def set_batch_coa(self):
		if self.certificate_of_analysis:
			frappe.db.set_value("Batch", self.batch_no, "certificate_of_analysis", self.certificate_of_analysis)

	def get_purchase_item_details(self):
		doc = frappe.get_doc(self.reference_type, self.reference_name)
		for item in doc.items:
			if item.item_code == self.item_code:
				self.set("manufacturer_name", doc.supplier)
				self.set("uom", item.uom)
				self.set("qty", item.qty)
				self.set("manufacturer_website", frappe.db.get_value("Supplier", doc.supplier, "website"))

def item_query(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("from"):
		from frappe.desk.reportview import get_match_cond
		mcond = get_match_cond(filters["from"])
		cond, qi_condition = "", "and (quality_inspection is null or quality_inspection = '')"

		if filters.get('from') in ['Purchase Invoice Item', 'Purchase Receipt Item']\
				and filters.get("inspection_type") != "In Process":
			cond = """and item_code in (select name from `tabItem` where
				inspection_required_before_purchase = 1)"""
		elif filters.get('from') in ['Sales Invoice Item', 'Delivery Note Item']\
				and filters.get("inspection_type") != "In Process":
			cond = """and item_code in (select name from `tabItem` where
				inspection_required_before_delivery = 1)"""
		elif filters.get('from') == 'Stock Entry Detail':
			cond = """and s_warehouse is null"""

		if filters.get('from') in ['Supplier Quotation Item']:
			qi_condition = ""

		return frappe.db.sql(""" select item_code from `tab{doc}`
			where parent=%(parent)s and docstatus < 2 and item_code like %(txt)s
			{qi_condition} {cond} {mcond}
			order by item_code limit {start}, {page_len}""".format(doc=filters.get('from'),
			parent=filters.get('parent'), cond = cond, mcond = mcond, start = start,
			page_len = page_len, qi_condition = qi_condition),
			{'parent': filters.get('parent'), 'txt': "%%%s%%" % txt})

def quality_inspection_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.get_all('Quality Inspection',
		limit_start=start,
		limit_page_length=page_len,
		filters = {
			'docstatus': 1,
			'name': ('like', '%%%s%%' % txt),
			'item_code': filters.get("item_code"),
			'reference_name': ('in', [filters.get("reference_name", ''), ''])
		}, as_list=1)

@frappe.whitelist()
def make_quality_inspection(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.inspected_by = frappe.session.user
		doc.get_quality_inspection_template()

	doc = get_mapped_doc("BOM", source_name, {
		'BOM': {
			"doctype": "Quality Inspection",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map": {
				"name": "bom_no",
				"item": "item_code",
				"stock_uom": "uom",
				"stock_qty": "qty"
			},
		}
	}, target_doc, postprocess)

	return doc
