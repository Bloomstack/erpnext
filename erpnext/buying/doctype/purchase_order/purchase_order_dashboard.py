from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'purchase_order',
		'non_standard_fieldnames': {
			'Journal Entry': 'reference_name',
			'Payment Entry': 'reference_name',
			'Auto Repeat': 'reference_document'
		},
		'internal_links': {
			'Material Request': ['items', 'material_request'],
			'Sales Order': ['items', 'sales_order'],
			'Production Plan': ['items', 'production_plan'],
			'Supplier Quotation': ['items', 'supplier_quotation'],
			'Project': ['items', 'project']
		},
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Purchase Receipt', 'Purchase Invoice']
			},
			{
				'label': _('Payment'),
				'items': ['Payment Entry', 'Journal Entry']
			},
			{
				'label': _('Reference'),
				'items': ['Material Request', 'Sales Order', 'Production Plan', 'Supplier Quotation', 'Project', 'Auto Repeat']
			},
			{
				'label': _('Sub-contracting'),
				'items': ['Stock Entry']
			},
		]
	}
