frappe.ready(() => {
    ongoing_topic = decodeURIComponent(getURLParameter(location.href, "content"));
    $('.content-name').filter(function () {
        return $(this).attr("id") == ongoing_topic
    }).css({
        'color': 'black'
    }).parent('li').addClass('active-parent');

    function getURLParameter(url, name) {
        return (RegExp(name + '=' + '(.+?)(&|$)').exec(url) || [, null])[1];
    }

    completed_topic = decodeURIComponent(getURLParameter(location.href, "course"));
    frappe.call({
        method: "erpnext.www.lms.content.get_completed_topic_list",
        args: {
            course_name: completed_topic
        },
        callback: (r) => {
            console.log(r);
            r.message.forEach(e => {
                console.log(e.content);
                $('.content-name').filter(function () {
                    return $(this).attr("id") == e.content
                }).css({
                    'color': 'blue'
                })

            });
        }
    });
})