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
	context.contents = get_contents(context.topic, course, program)
	context.has_access =  utils.allowed_program_access(program)
	context.has_super_access = utils.has_super_access()
	context.total_progress = calculate_contents_progress(context.contents)
	context.ongoing_topic = get_ongoing_topic(context.contents)

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

def calculate_contents_progress(contents):
	""" Fetch topic's content running status from Course Activity

	Arg:
		contents: It gives how many topic's contents are completed and how many of them are in start state

	Return:
		total_progress: Returns topic's content progress based on total contents of topic and how many topic's contents are completed among them.
	"""

	total_content = len(contents)
	completed_content = 0
	for content in contents:
		if content.get("completed"):
			completed_content = completed_content + 1
	total_progress = int((completed_content * 100) / total_content)
	return total_progress

def get_ongoing_topic(contents):
	ongoing_content = None
	ongoing_topics = [content for content in contents if not content.get("completed")]
	if len(contents) != len(ongoing_topics) and len(ongoing_topics) > 0:
		ongoing_content = ongoing_topics[0].get('content')
	return ongoing_content
