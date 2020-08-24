from frappe import _


def get_data():
	return {
		'fieldname': 'investor_name',
		'non_standard_fieldnames': {
			'Lead': 'party_name',
			'Opportunity': 'party_name'
		},
		'transactions': [
			{
				'items': ['Lead', 'Opportunity']
			}
		]
	}
