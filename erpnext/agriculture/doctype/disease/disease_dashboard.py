from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'disease',
		'transactions': [
			{
				'label': _('Disease Diagnosis'),
				'items': ['Plant Disease Diagnosis']
			}
		]
	}
