from __future__ import unicode_literals
from frappe import _


def get_data():
	return {
		'fieldname': 'material_request',
		'internal_links': {
			'Sales Order': ['items', 'sales_order'],
			'Production Plan': ['items', 'production_plan'],
		},
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Request for Quotation', 'Supplier Quotation', 'Purchase Order', 'Stock Entry', 'Pick List']
			},
			{
				'label': _('Manufacturing'),
				'items': ['Work Order']
			},
			{
				'label': _('Reference'),
				'items': ['Sales Order', 'Production Plan']
			},
		]
	}