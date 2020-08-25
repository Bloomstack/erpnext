/* eslint-disable */
// rename this file from _test_[name] to test_[name] to activate
// and remove above this line

QUnit.test("test: Plant Batch", function (assert) {
	let done = assert.async();

	// number of asserts
	assert.expect(1);

	frappe.run_serially([
		// insert a new Plant Batch
		() => frappe.tests.make('Plant Batch', [
			// values to be set
			{ title: 'Basil from seed 2017' },
			{ strain: 'Basil from seed' },
			{ start_date: '2017-11-11' },
			{ location: 'Basil Farm'},
			{ cycle_type: 'Less than a year' }
		]),
		() => assert.equal(cur_frm.doc.name, 'Basil from seed 2017'),
		() => done()
	]);
});
