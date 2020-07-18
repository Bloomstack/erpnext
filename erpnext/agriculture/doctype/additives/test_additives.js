/* eslint-disable */
// rename this file from _test_[name] to test_[name] to activate
// and remove above this line

QUnit.test("test: Additives", function (assert) {
	let done = assert.async();

	// number of asserts
	assert.expect(1);

	frappe.run_serially([
		// insert a new Item
		() => frappe.tests.make('Item', [
			// values to be set
			{item_code: 'Urea'},
			{item_name: 'Urea'},
			{item_group: 'Additives'}
		]),
		// insert a new Additives
		() => frappe.tests.make('Additives', [
			// values to be set
			{Additives_name: 'Urea'},
			{item: 'Urea'}
		]),
		() => {
			assert.equal(cur_frm.doc.name, 'Urea');
		},
		() => done()
	]);

});
