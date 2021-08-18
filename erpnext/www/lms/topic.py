from __future__ import unicode_literals
import erpnext.education.utils as utils
import frappe

no_cache = 1

def get_context(context):
	try:
		course = frappe.form_dict['course']
		program = frappe.form_dict['program']
		topic = frappe.form_dict['topic']
	except KeyError:
		frappe.local.flags.redirect_location = '/lms'
		raise frappe.Redirect

	context.program = program
	context.course = course
	context.topic = frappe.get_doc("Topic", topic)
	context.student = utils.get_current_student()
	course_details = frappe.get_doc('Course',course)
	context.course_topics = course_details.get_topics()

	context.contents = get_contents(context.topic, course, program)
	context.has_access =  utils.allowed_program_access(program)
	context.has_super_access = utils.has_super_access()
	context.ongoing_topic = get_ongoing_topic(context.contents)
	context.total_progress = utils.get_total_program_progress(context.course_topics, course, context.student)
	# Get all topics
	content_list = []
	for t in context.course_topics:
		for topic_content in t.topic_content:
			content_list.append({'content_type':topic_content.content_type, 'content':topic_content.content})

	context.length = len(content_list)
	context.completed_topics = utils.get_completed_topic_list(course)

	# Set context for progress numbers
	context.position = len(context.completed_topics)

	# Set context for navigation
	context.previous = utils.get_previous_content(content_list, context.position)
	context.next = utils.get_next_content(content_list, context.position-1)


def get_contents(topic, course, program):
	student = utils.get_current_student()
	if student:
		course_enrollment = utils.get_or_create_course_enrollment(course, program)
	contents = topic.get_contents()
	progress = []
	if contents:
		for content in contents:
			if content.doctype in ('Article', 'Video'):
				if student:
					status = utils.check_content_completion(content.name, content.doctype, course_enrollment.name)
				else:
					status = True
				progress.append({'content': content, 'content_type': content.doctype, 'completed': status})
			elif content.doctype == 'Quiz':
				if student:
					status, score, result = utils.check_quiz_completion(content, course_enrollment.name)
				else:
					status = False
					score = None
					result = None
				progress.append({'content': content, 'content_type': content.doctype, 'completed': status, 'score': score, 'result': result})
	return progress

def get_ongoing_topic(contents):
	ongoing_content = None
	ongoing_topics = [content for content in contents if not content.get("completed")]
	if len(contents) != len(ongoing_topics) and len(ongoing_topics) > 0:
		ongoing_content = ongoing_topics[0].get('content')
	return ongoing_content
