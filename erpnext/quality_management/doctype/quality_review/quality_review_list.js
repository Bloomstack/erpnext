frappe.listview_settings['Quality Review'] = {
	add_fields: ["action", "status"],
	get_indicator: function(doc)
	{
		if(doc.action == "No Action") {
			return [__("No Action"), "green", "action,=,No Action"];
		} else if (doc.action == "Action Initialised") {
			return [__("Action Initialised"), "red", "action,=,Action Initialised"];
		} else if (doc.status === "Open") {
			return [__("Open"), "red", "status,=,Open"];
		} else if (doc.status === "Closed") {
			return [__("Closed"), "green", "status,=,Closed"];
		}
	}
};