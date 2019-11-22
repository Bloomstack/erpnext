from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'packing_slip',
		'internal_links': {
			'Sales Order': 'sales_order',
			'Delivery Note': ['items', 'delivery_note']
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': ['Sales Order']
			},
			{
				'label': _('Fulfillment'),
				'items': ['Delivery Note']
			}
		]
	}
