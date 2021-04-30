from __future__ import unicode_literals
import erpnext.education.utils as utils
import frappe
from frappe import _

no_cache = 1

def get_context(context):
	try:
		program = frappe.form_dict['program']
	except KeyError:
		frappe.local.flags.redirect_location = '/lms'
		raise frappe.Redirect

	context.education_settings = frappe.get_single("Education Settings")
	context.program = get_program(program)
	context.courses = [frappe.get_doc("Course", course.course) for course in context.program.courses]
	context.has_access = utils.allowed_program_access(program)
	context.has_super_access = utils.has_super_access()
	context.progress = get_course_progress(context.courses, program)
	context.total_progress = calculate_course_progress(context.progress)

def get_program(program_name):
	try:
		return frappe.get_doc('Program', program_name)
	except frappe.DoesNotExistError:
		frappe.throw(_("Program {0} does not exist.".format(program_name)))

def get_course_progress(courses, program):
	progress = {course.name: utils.get_course_progress(course, program) for course in courses}
	return progress

def calculate_course_progress(course_progress):
	""" Fetch course running status from course list

	Arg:
		course_progress: It gives how many courses are completed and how many of them have start status

	Return:
		total_progress: Returns course progress based on total courses and how many courses are completed among them.
	"""
	total_courses = len(course_progress)
	completed_courses = 0
	for progress in course_progress:
		if course_progress.get(progress).get("completed"):
			completed_courses = completed_courses + 1
	total_progress = int((completed_courses * 100) / total_courses)
	return total_progress