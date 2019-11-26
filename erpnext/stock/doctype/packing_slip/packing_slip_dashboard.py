from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'packing_slip',
		'non_standard_fieldnames': {
			'Stock Entry': 'packing_slip_no',
			'Delivery Note': 'against_packing_slip'
		},
		'internal_links': {
			'Sales Order': 'sales_order'
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': ['Sales Order', 'Stock Entry']
			},
			{
				'label': _('Fulfillment'),
				'items': ['Delivery Note']
			}
		]
	}
