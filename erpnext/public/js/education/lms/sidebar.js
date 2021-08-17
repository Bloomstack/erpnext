frappe.ready(() => {
	var ongoing_topic = decodeURIComponent(getURLParameter(location.href, "content"));
	$('.content-name').filter(function () {
		return $(this).attr("id") == ongoing_topic;
	}).css({
		'color': 'black'
	}).parent('li').addClass('active-parent');

	function getURLParameter(url, name) {
		return (RegExp(name + '=' + '(.+?)(&|$)').exec(url) || [, null])[1];
	}

	var completed_topic = decodeURIComponent(getURLParameter(location.href, "course"));
	frappe.call({
		method: "erpnext.education.utils.get_completed_topic_list",
		args: {
			course_name: completed_topic
		},
		callback: (r) => {
			r.message.forEach(e => {
				$('.content-name').filter(function () {
					return $(this).attr("id") == e.content || e.quiz;
				}).css({
					'color': 'blue'
				}).addClass('completed-article').parent('li').addClass('completed-parent');
			});
		}
	});
});