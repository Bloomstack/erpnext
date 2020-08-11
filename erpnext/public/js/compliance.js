$.each(["Customer", "Supplier", "Company"], function (i, doctype) {
	frappe.ui.form.on(doctype, {
		refresh: (frm) => {
			frm.set_query("license", "licenses", (doc, cdt, cdn) => {
				const set_licenses = doc.licenses.map(license => license.license);
				return {
					query: "erpnext.compliance.doctype.compliance_info.compliance_info.get_active_licenses",
					filters: {
						set_licenses: set_licenses
					}
				}
			});
		}
	});
});