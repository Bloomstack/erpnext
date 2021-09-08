// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.projects");

frappe.ui.form.on("Task", {
	setup: function (frm) {
		frm.set_query("default_project", function () {
			return {
				query: "erpnext.projects.doctype.task.task.get_project"
			}
		});

		frm.set_query("assign_to", () => {
			return {
				query: "erpnext.projects.doctype.task.task.get_team_members",
				filters: {
					team: frm.doc.team
				}
			};
		});

		frm.make_methods = {
			'Timesheet': () => frappe.model.open_mapped_doc({
				method: 'erpnext.projects.doctype.task.task.make_timesheet',
				frm: frm
			})
		}
	},

	onload: function (frm) {
		frm.set_query("task", "depends_on", function () {
			let filters = {
				name: ["!=", frm.doc.name]
			};
			if (frm.doc.default_project) filters["default_project"] = frm.doc.default_project;
			return {
				filters: filters
			};
		})
	},

	refresh: function (frm) {
		frm.set_query("parent_task", { "is_group": 1 });
		frappe.model.with_doctype('Task', () => {
			const status_df = frappe.meta.get_docfield("Task", "status", frm.docname);
			frm.set_df_property("status", "options", status_df.options, frm.docname, "projects");
		});
		if (frm.is_new()) {
			frm.toggle_display("default_project", 0);
		}
	},
	is_group: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.task.task.check_if_child_exists",
			args: {
				name: frm.doc.name
			},
			callback: function (r) {
				if (r.message.length > 0) {
					frappe.msgprint(__(`Cannot convert it to non-group. The following child Tasks exist: ${r.message.join(", ")}.`));
					frm.reload_doc();
				}
			}
		})
	},

	validate: function (frm) {
		frm.doc.default_project && frappe.model.remove_from_locals("Default_Project",
			frm.doc.default_project);
	},

	default_project: (frm) => {
		if (frm.doc.default_project && frm.doc.billable === 0) {
			frappe.db.get_value("Default_Project", { "name": frm.doc.default_project }, "billable", (r) => {
				if (r && r.billable === 1) {
					frm.set_value("billable", 1);
				}
			});
		}
	}
});
