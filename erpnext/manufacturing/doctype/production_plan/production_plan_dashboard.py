from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'production_plan',
		'internal_links': {
			'Sales Order': ['po_items', 'sales_order']
		},
		'transactions': [
			{
				'label': _('Transactions'),
				'items': ['Work Order', 'Material Request']
			},
			{
				'label': _('Reference'),
				'items': ['Sales Order']
			},
		]
	}