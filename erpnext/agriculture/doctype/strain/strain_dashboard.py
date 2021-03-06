from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'strain',
		'transactions': [
			{
				'label': _('Cultivation & Harvesting'),
				'items': ['Plant', 'Plant Batch', 'Harvest']
			},
			{
				'label': _('Diseases & Additives'),
				'items': ['Plant Disease Diagnosis', 'Plant Additive Log']
			}
		]
	}
