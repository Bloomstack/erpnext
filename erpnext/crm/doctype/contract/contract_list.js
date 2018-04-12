frappe.listview_settings['Contract'] = {
    add_fields: ["custom_status"],
    get_indicator: function (doc) {
        if (doc.custom_status == "Unsigned") {
            return [__(doc.custom_status), "orange", "custom_status,=," + doc.custom_status];
        } else if (doc.custom_status == "Active") {
            return [__(doc.custom_status), "green", "custom_status,=," + doc.custom_status];
        } else if (doc.custom_status == "Inactive") {
            return [__(doc.custom_status), "darkgrey", "custom_status,=," + doc.custom_status];
        }
    },
};