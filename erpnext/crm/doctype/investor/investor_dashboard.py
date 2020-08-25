from frappe import _


def get_data():
	return {
		'heatmap': True,
		'heatmap_message': _('This is based on the transaction of this Investor'),
		'fieldname': 'name',
		'non_standard_fieldnames': {
			'Lead': 'lead_name',
			'Opportunity': 'customer_name'
		},
		'transactions': [
			{
				'label': _('Transactions'),
				'items': ['Lead', 'Opportunity']
			}
		]
	}
