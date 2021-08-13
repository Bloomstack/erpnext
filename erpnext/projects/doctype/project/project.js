// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.ui.form.on("Project", {
	setup(frm) {
		frm.make_methods = {
			'Timesheet': () => {
				open_form(frm, "Timesheet", "Timesheet Detail", "time_logs");
			},
			'Purchase Order': () => {
				open_form(frm, "Purchase Order", "Purchase Order Item", "items");
			},
			'Purchase Receipt': () => {
				open_form(frm, "Purchase Receipt", "Purchase Receipt Item", "items");
			},
			'Purchase Invoice': () => {
				open_form(frm, "Purchase Invoice", "Purchase Invoice Item", "items");
			},
			'Task': () => {
				open_form(frm, "Task", "Task Project", "projects");
			}
		};
	},
	onload: function (frm) {
		var so = frappe.meta.get_docfield("Project", "sales_order");
		so.get_route_options_for_new_doc = function (field) {
			if (frm.is_new()) return;
			return {
				"customer": frm.doc.customer,
				"project_name": frm.doc.name
			};
		};

		frm.set_query('customer', 'erpnext.controllers.queries.customer_query');

		frm.set_query("user", "users", function () {
			return {
				query: "erpnext.projects.doctype.project.project.get_users_for_project"
			};
		});

		// sales order
		frm.set_query('sales_order', function () {
			var filters = {
				'project': ["in", frm.doc.__islocal ? [""] : [frm.doc.name, ""]]
			};

			if (frm.doc.customer) {
				filters["customer"] = frm.doc.customer;
			}

			return {
				filters: filters
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.__islocal) {
			frm.web_link && frm.web_link.remove();
		} else {
			frm.add_web_link("/projects?project=" + encodeURIComponent(frm.doc.name));
		}
		frm.events.set_buttons(frm);
	},

	set_buttons: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Duplicate Project with Tasks'), () => {
				frm.events.create_duplicate(frm);
			});

			frm.add_custom_button(__('Completed'), () => {
				frm.events.set_status(frm, 'Completed');
			}, __('Set Status'));

			frm.add_custom_button(__('Cancelled'), () => {
				frm.events.set_status(frm, 'Cancelled');
			}, __('Set Status'));
		}

		if (frappe.model.can_read("Task")) {
			frm.add_custom_button(__("Gantt Chart"), function () {
				frappe.route_options = {
					"project": frm.doc.name
				};
				frappe.set_route("List", "Task", "Gantt");
			});

			frm.add_custom_button(__("Kanban Board"), () => {
				frappe.call('erpnext.projects.doctype.project.project.create_kanban_board_if_not_exists', {
					project: frm.doc.project_name
				}).then(() => {
					frappe.set_route('List', 'Task', 'Kanban', frm.doc.project_name);
				});
			});
		}
	},

	create_duplicate: function(frm) {
		return new Promise(resolve => {
			frappe.prompt('Project Name', (data) => {
				frappe.xcall('erpnext.projects.doctype.project.project.create_duplicate_project',
					{
						prev_doc: frm.doc,
						project_name: data.value
					}).then(() => {
					frappe.set_route('Form', "Project", data.value);
					frappe.show_alert(__("Duplicate project has been created"));
				});
				resolve();
			});
		});
	},

	set_status: function(frm, status) {
		frappe.confirm(__('Set Project and all Tasks to status {0}?', [status.bold()]), () => {
			frappe.xcall('erpnext.projects.doctype.project.project.set_project_status',
				{project: frm.doc.name, status: status}).then(() => { /* page will auto reload */ });
		});
	},

	collect_progress: function(frm) {
		if (frm.doc.collect_progress) {
			frm.set_df_property("message", "reqd", 1);
		}
	},

	project_template: (frm) => {
		if (frm.is_new() && frm.doc.project_template && frm.doc.billable === 0) {
			frappe.db.get_value("Project Template", { "name": frm.doc.project_template }, "billable", (r) => {
				if (r && r.billable === 1) {
					frm.set_value("billable", r.billable);
				}
			});
		}
	},

	project_type: (frm) => {
		if (frm.doc.project_type && frm.doc.billable === 0) {
			frappe.db.get_value("Project Type", { "name": frm.doc.project_type }, "billable", (r) => {
				if (r && r.billable === 1) {
					frm.set_value("billable", r.billable);
				}
			});
		}
	},

	freeze: (frm) => {
		let confirm_message = "";
		frappe.call({
			method: "frappe.desk.form.linked_with.get_submitted_linked_docs",
			args: {
				doctype: frm.doc.doctype,
				name: frm.doc.name,
				only_submittable: false,
				skip_doctypes: ["Activity Log", "Comment", "Timesheet"]
			},
			freeze: true,
			callback: (r) => {
				if (!r.exc && r.message.count > 0) {
					// add confirmation message for cancelling all linked docs
					let links_text = "";
					let links = r.message.docs;
					const doctypes = Array.from(new Set(links.map((link) => link.doctype)));

					for (let doctype of doctypes) {
						let docnames = links
							.filter((link) => link.doctype === doctype)
							.map((link) => frappe.utils.get_form_link(link.doctype, link.name, true))
							.join(", ");
						links_text += `<li><strong>${doctype}</strong>: ${docnames}</li>`;

					}
					links_text = "<ul>" + links_text + "</ul>";
					confirm_message = __(`{0} is linked with the following documents: {1}`, [frm.doc.name.bold(), links_text]);
					frappe.confirm(__(`{0} Do you want to set them as <strong>{1}</strong> too?`, [confirm_message, frm.doc.freeze ? "Freeze" : "Not Freeze"]),
						() => {
							frappe.call({
								method: "erpnext.projects.doctype.project.project.update_task_projects",
								args: {
									ref_dt: frm.doctype,
									ref_dn: frm.doc.name,
									freeze: frm.doc.freeze
								},
								callback: (r) => {
									frm.save();
								}
							})
						},
						() => {
							frm.save();
						}
					);
				}
			}
		});
	}

});

function open_form(frm, doctype, child_doctype, parentfield) {
	frappe.model.with_doctype(doctype, () => {
		let new_doc = frappe.model.get_new_doc(doctype);

		// add a new row and set the project
		let new_child_doc = frappe.model.get_new_doc(child_doctype);
		new_child_doc.project = frm.doc.name;
		new_child_doc.parent = new_doc.name;
		new_child_doc.parentfield = parentfield;
		new_child_doc.parenttype = doctype;
		if (doctype === "Timesheet") {
			new_child_doc.billable = frm.doc.billable;
		}
		new_doc[parentfield] = [new_child_doc];

		frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
	});

}