from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'reference_name',
		'transactions': [
			{
				'label': _('Nonsubscribers'),
				'items': ['Email Unsubscribe']
			}
		]
	}
