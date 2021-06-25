from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'transactions': [
			{
				'label': _('Quotation'),
				'items': ['Quotation']
			},
			{
				'label': _('Sales Order'),
				'items': ['Sales Order']
			},
		]
	}