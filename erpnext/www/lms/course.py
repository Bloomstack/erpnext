from __future__ import unicode_literals
import erpnext.education.utils as utils
import frappe

no_cache = 1

def get_context(context):
	try:
		program = frappe.form_dict['program']
		course_name = frappe.form_dict['name']
	except KeyError:
		frappe.local.flags.redirect_location = '/lms'
		raise frappe.Redirect

	context.education_settings = frappe.get_single("Education Settings")
	course = frappe.get_doc('Course', course_name)
	context.program = program
	context.course = course

	context.topics = course.get_topics()
	context.has_access =  utils.allowed_program_access(context.program)
	context.has_super_access = utils.has_super_access()
	context.progress = get_topic_progress(context.topics, course, context.program)
	context.ongoing_topic = get_ongoing_topic(context.topics,context.progress)
	context.total_progress = utils.get_total_program_progress(context.topics,course_name)


def get_topic_progress(topics, course, program):
	progress = {topic.name: utils.get_topic_progress(topic, course.name, program) for topic in topics}
	return progress

def get_ongoing_topic(topics, progress):
	ongoing_topic = None
	for topic in progress:
		if progress.get(topic).get("started") == True and progress.get(topic).get("completed") == False:
			ongoing_topic = topic
	return ongoing_topic

@frappe.whitelist(allow_guest=True)
def get_content_details(type, content_name):
	content = frappe.get_doc(type, content_name)
	return content

@frappe.whitelist(allow_guest=True)
def get_completed_topic_list(course_name):
	completed_topic = frappe.get_all("Course Activity", filters={"course": course_name},fields= ["content","content_type","enrollment"])
	return completed_topic
