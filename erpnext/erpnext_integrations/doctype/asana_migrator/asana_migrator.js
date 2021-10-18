// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asana Migrator', {

	refresh: function (frm) {
		frm.get_field("tasks_view").$wrapper.empty();
		frm.events.set_data_field_property(frm);
		frm.events.crete_task_view(frm);
		frm.events.update_primary_action(frm);

		if (frm.is_new()) {
			frm.events.get_workspaces(frm);
		}
		frm.events.setup_progress(frm);
	},

	onload_post_render(frm) {
		frm.events.update_primary_action(frm);
	},

	update_primary_action(frm) {
		if (frm.is_new()) {
			frm.enable_save();
			return;
		}
		let statues = ["Pending", "Failed"];
		frm.disable_save();
		if (!frm.is_new() && !frm.doc.row_data) {
			frm.page.set_primary_action('Get Tasks', () => frm.events.get_tasks(frm));
		} else if (statues.includes(frm.doc.status) && frm.doc.row_data) {
			frm.page.set_primary_action('Import Tasks', () => frm.events.import_tasks(frm));
		}

		if (frm.doc.status == "Completed") {
			frm.disable_save();
		}
	},

	setup_progress: function (frm) {
		frappe.realtime.on('fetching_task', (data) => {
			if (data.progress < 100) {
				frm.dashboard.show_progress('Get Task', data.progress, data.label);
			} else {
				cur_frm.dashboard.hide_progress();
				cur_frm.refresh();
			}
		});
	},

	set_data_field_property: function (frm) {
		if (frm.doc.workspace_options) {
			frm.set_df_property("workspace", "options", JSON.parse(frm.doc.workspace_options));
			frm.set_df_property("project", "options", JSON.parse(frm.doc.project_options));
			frm.doc.workspace = frm.doc.selected_workspace;
			frm.set_df_property("workspace", "read_only", 1);
			frm.doc.project = frm.doc.selected_project;
		}

		if (frm.doc.project_options) {
			frm.set_df_property("project", "read_only", 1);
		}

	},

	crete_task_view: function (frm) {
		if (frm.doc.row_data) {
			frm.events.load_dependencies(frm);
		} else {
			frm.get_field("tasks_view").$wrapper.empty();
		}
	},

	workspace: function (frm) {
		let workspaces = JSON.parse(frm.doc.workspace_options);
		let global_id;
		for (let idx in workspaces){
			let data = workspaces[idx]
			if (data.name == frm.doc.workspace){
				global_id = data.gid
			} 
		}
		frm.events.get_projects(frm, global_id);

		// saving Options as Workspace value as options are Dynamic.
		frm.doc.selected_workspace = frm.doc.workspace;
	},

	get_workspaces: function (frm) {
		frappe.call({
			method: "erpnext.erpnext_integrations.doctype.asana_migrator.asana_migrator.get_workspaces",
			freeze: true,
			freeze_message: __("Getting Workspaces..."),
		}).then(r => {
			let options = [];
			if (r.message) {
				for (let idx in r.message) {
					options.push(r.message[idx].name)
				}
				frm.set_df_property("workspace", "options", options);
				frm.set_value("workspace", options[0]);
				// saving Options as Worksapces option is Dynamic.
				frm.doc.workspace_options = JSON.stringify(r.message);
			}
		});
	},

	get_projects: function (frm, global_id) {
		frappe.call({
			method: "erpnext.erpnext_integrations.doctype.asana_migrator.asana_migrator.get_projects",
			freeze: true,
			freeze_message: __("Getting Projects..."),
			args: {
				global_id: global_id
			}
		}).then(r => {
			let options = [];
			if (r.message) {
				for (let idx in r.message) {
					options.push(r.message[idx].name);
				}
				frm.set_df_property("project", "options", options);
				frm.set_value("project", options[0]);

				// saving Options as Projects option is Dynamic.
				frm.doc.project_options = JSON.stringify(r.message);
			}
		});
	},

	get_tasks: function (frm) {
		if (frm.doc.workspace && frm.doc.project) {
			return frappe.call({
				method: 'get_tasks',
				doc: frm.doc,
				callback: function () {
					frm.refresh();
					frm.dirty();
					frm.save();
					frm.events.update_primary_action(frm);
				}
			});
		}
	},

	import_tasks: function (frm) {
		if (frm.doc.row_data) {
			let checked_row_index = frm.datatable.rowmanager.getCheckedRows();
			let tasks_to_import = [];
			let comments_to_import = {};
			let comments = JSON.parse(frm.doc.tasks_comment);

			for (let idx in checked_row_index) {
				let data_index = checked_row_index[idx];
				let task_data = frm.datatable.options.data[data_index] || [];

				let task_gid = String(task_data.global_id) || '';
				let task_comments = comments[task_gid];
				tasks_to_import.push(task_data);
				if (task_comments) {
					comments_to_import[task_gid] = task_comments;
				}
			}
			if (tasks_to_import.length) {
				return frappe.call({
					method: 'import_tasks',
					doc: frm.doc,
					args: {
						tasks_to_import,
						comments_to_import
					},
					callback: function () {
						frm.refresh();
					}
				});
			} else {
				frappe.msgprint(__("Please select Tasks from Datatable to import"));
			}


		}
	},

	project: function (frm) {
		// saving Projects value as options are Dynamic.
		frm.doc.selected_project = frm.doc.project;
	},

	load_dependencies: function () {
		const assets = [
			"/assets/frappe/css/frappe-datatable.css",
			"/assets/frappe/js/lib/clusterize.min.js",
			"/assets/frappe/js/lib/Sortable.min.js",
			"/assets/frappe/js/lib/frappe-datatable.js"
		];
		frappe.require(assets, () => {
			this.make_datatable(cur_frm);
		});
	},

	make_datatable: function (frm) {
		let editable = true;
		if (frm.doc.status == "Completed") {
			editable = false;
		}
		let columns = frm.events.get_columns(editable);
		let row = JSON.parse(frm.doc.row_data);
		frm.get_field("tasks_view").$wrapper.append(`<div>
			<span class="indicator whitespace-nowrap blue">
				<span>Sub-Tasks will be imported Automatically</span>
			</span>
		</div>
		<hr>`);
		frm.get_field("tasks_view").$wrapper.append('<div id="datatable"></div>');
		frm.datatable = new DataTable('#datatable', {
			columns: columns,
			data: row,
			addCheckboxColumn: true,
			treeView: true,
			getEditor: function (colIndex, rowIndex, value, parent) {
				const control = frappe.ui.form.make_control({
					parent: parent,
					df: {
						label: '',
						fieldname: "task",
						fieldtype: 'Data',
						options: "task"
					},
					render_input: true,
					only_input: true,
				});

				return cur_frm.events.bind_events(cur_frm, control, colIndex, rowIndex);
			},
		});
	},

	bind_events: (frm, control, colIndex, rowIndex) => {
		return {
			// called when cell is being edited
			initValue(value) {
				control.input.focus();
				control.input.value = value;
			},
			// called when cell value is set
			setValue(newValue) {
				// subtracting two because first two columns are for sno and checkbox
				let key = frm.datatable.options.columns[colIndex - 2].id;
				frm.datatable.options.data[rowIndex][key] = newValue;
				frm.datatable.refresh();

				// update docs accordingly
				frm.doc.row_data = JSON.stringify(frm.datatable.options.data);
				frm.dirty();
				frm.page.set_primary_action('Save', () => frm.save());
				control.input.value = newValue;
			},
			// value to show in cell
			getValue() {
				return control.input.value;
			}
		};
	},

	get_columns: (editable) => {
		return [
			{
				content: 'Name',
				id: 'name',
				editable: editable,
				resizable: true,
				width: 200
			},
			{
				content: 'Global Id',
				id: 'global_id',
				editable: false,
				resizable: true,
			},
			{
				content: 'Notes',
				id: 'notes',
				editable: editable,
				resizable: true,
				width: 200
			},
			{
				content: 'Assignee',
				editable: false,
				id: 'assignee'
			},
			{
				content: 'Status',
				editable: false,
				id: 'status'
			},
			{
				content: "Completed On",
				editable: false,
				id: "completed_on"
			}
		];
	}
});
