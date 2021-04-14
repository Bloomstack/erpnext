from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'batch_no',
		'transactions': [
			{
				'label': _('Buy'),
				'items': ['Material Request', 'Purchase Invoice', 'Purchase Receipt']
			},
			{
				'label': _('Sell'),
				'items': ['Sales Order', 'Sales Invoice', 'Delivery Note']
			},
			{
				'label': _('Move'),
				'items': ['Stock Entry']
			},
			{
				'label': _('Quality'),
				'items': ['Quality Inspection']
			},
			{
				'label': _('Package Tag'),
				'items': ['Package Tag']
			}
		]
	}
