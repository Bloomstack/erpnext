from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'plant_batch',
		'transactions': [
			{
				'label': _('Cultivation & Harvesting'),
				'items': ['Plant', 'Harvest']
			},
			{
				'label': _('Plant Log'),
				'items': ['Plant Additive Log', 'Plant Disease Diagnosis', 'Destroyed Plant Log']
			}
		]
	}
