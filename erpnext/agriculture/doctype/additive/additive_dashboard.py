from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'additive',
		'transactions': [
			{
				'label': _('Additive Log'),
				'items': ['Plant Additive Log']
			}
		]
	}
