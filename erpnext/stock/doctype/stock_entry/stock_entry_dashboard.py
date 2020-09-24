from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'stock_entry',
		'non_standard_fieldnames': {
			'Quality Inspection': 'reference_name'
		},
		'internal_links': {
			'Material Request': ['items', 'material_request'],
			'Purchase Receipt': ['items', 'reference_purchase_receipt'],
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': ['Quality Inspection', 'Material Request', 'Purchase Receipt']
			}
		]

	}
