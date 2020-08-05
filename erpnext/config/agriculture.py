from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Cultivation & Harvesting"),
			"items": [
				{
					"type": "doctype",
					"name": "Strain",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Plant Batch",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Plant",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Harvest",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Location",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Plant Tag",
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Diseases & Additives"),
			"items": [
				{
					"type": "doctype",
					"name": "Plant Disease Diagnosis",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Plant Additive Log",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Disease",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Additive",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Additive Type",
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Analytics"),
			"items": [
				{
					"type": "doctype",
					"name": "Plant Analysis",
				},
				{
					"type": "doctype",
					"name": "Soil Analysis",
				},
				{
					"type": "doctype",
					"name": "Water Analysis",
				},
				{
					"type": "doctype",
					"name": "Soil Texture",
				},
				{
					"type": "doctype",
					"name": "Weather",
				},
				{
					"type": "doctype",
					"name": "Agriculture Analysis Criteria",
				}
			]
		},
	]