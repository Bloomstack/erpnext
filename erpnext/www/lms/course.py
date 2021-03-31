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
	context.progress = get_topic_progress(context.topics, course, context.program)
	context.total_progress = calculate_topic_progress(context.topics,context.progress)


def get_topic_progress(topics, course, program):
	progress = {topic.name: utils.get_topic_progress(topic, course.name, program) for topic in topics}
	return progress

def calculate_topic_progress(topics,topic_progress):
	total_topics = len(topics)
	completed_topic = 0
	for topic in topic_progress:
		if topic_progress[topic].get("completed"):
			completed_topic = completed_topic + 1
	total_progress = int((completed_topic * 100) / total_topic)
	return total_progress