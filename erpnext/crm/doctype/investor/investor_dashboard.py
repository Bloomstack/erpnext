from future import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': True,
		'heatmap_message': _('This is based on the Investor'),
		'fieldname': 'investor_name',
		'non_standard_fieldnames': {
			'Lead': 'party_name',
			'Opportunity': 'party_name'
		},
		'dynamic_links': {
			'party_name': ['Investor','Opportunity']
		},
		'transactions': [
			{
				'items': ['Lead', 'Opportunity']
			}
		]
	}