import frappe
from erpnext.portal.product_configurator.utils import (get_products_for_website, get_product_settings,
	get_field_filter_data, get_attribute_filter_data)
from erpnext.shopping_cart.product_info import get_product_info_for_website
from erpnext.stock.doctype.batch.batch import get_active_batch

sitemap = 1

def get_context(context):

	if frappe.form_dict:
		search = frappe.form_dict.search
		field_filters = frappe.parse_json(frappe.form_dict.field_filters)
		attribute_filters = frappe.parse_json(frappe.form_dict.attribute_filters)
	else:
		search = field_filters = attribute_filters = None

	context.products = get_products_for_website(field_filters, attribute_filters, search)
	for item in context.products:
		item["active_batch"] = get_active_batch(item.name)
		item["info"] = get_product_info_for_website(item.name)
		item_group = frappe.db.get_value('Item', item.name, 'item_group')
		item["group"] = frappe.scrub(item_group)

	product_settings = get_product_settings()
	context.field_filters = get_field_filter_data() \
		if product_settings.enable_field_filters else []

	context.attribute_filters = get_attribute_filter_data() \
		if product_settings.enable_attribute_filters else []

	context.product_settings = product_settings
	context.page_length = product_settings.products_per_page

	context.banner_image = frappe.db.get_single_value('Products Settings', 'banner_image')

	context.no_cache = 1