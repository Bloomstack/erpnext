from frappe import _


def get_data():
	return {
		'fieldname': 'investor_name',
		'non_standard_fieldnames': {
			'Lead': 'lead_name',
			'Opportunity': 'customer_name'
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': ['Lead', 'Opportunity']
			}
		]
	}
