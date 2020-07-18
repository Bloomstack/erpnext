frappe.listview_settings['Harvest'] = {
    add_fields: ["harvest_type"],

    get_indicator: function(doc) {
        if (doc.harvest_type == "Manicure") {
            return [__("Manicure"), "orange", "harvest_type,=, Manicure"];
        } else if (doc.harvest_type == "Harvest") {
            return [__("Harvest"), "green", "harvest_type,=, Harvest"];
        }
    }
};