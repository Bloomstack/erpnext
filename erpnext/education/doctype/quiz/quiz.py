# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import random, math
from frappe import _
from frappe.model.document import Document

class Quiz(Document):
	def validate(self):
		if self.passing_score > 100:
			frappe.throw(_("Passing Score value should be between 0 and 100"))
		self.validate_assessment_questions()

	def validate_assessment_questions(self):
		if self.assessment_questions > len(self.question):
			frappe.throw(_("Assessment Questions cannot be greater than the number of questions in Quiz"))

	def allowed_attempt(self, enrollment, quiz_name):
		if self.max_attempts ==  0:
			return True

		try:
			if len(frappe.get_all("Quiz Activity", {'enrollment': enrollment.name, 'quiz': quiz_name})) >= self.max_attempts:
				frappe.msgprint(_("Maximum attempts for this quiz reached!"))
				return False
			else:
				return True
		except Exception as e:
			return False


	def evaluate(self, response_dict, quiz_name):
		questions = [frappe.get_doc('Question', question.question_link) for question in self.question]
		answers = {q.name:q.get_answer() for q in questions}
		result = {}

		result = evaluate_response(answers, response_dict)

		# if assessment questions exists then evaluate on the basis of number of questions given in quiz
		if self.assessment_questions:
			score = math.ceil((sum(result.values()) * 100 ) / self.assessment_questions)
		else:
			score = (sum(result.values()) * 100 ) / len(answers)

		if score >= self.passing_score:
			status = "Pass"
		else:
			status = "Fail"
		return result, score, status

	def get_questions(self):
		quiz_questions = [frappe.get_doc('Question', question.question_link) for question in self.question]
		if self.assessment_questions:
			return random.sample(quiz_questions, self.assessment_questions)
		else:
			return quiz_questions


def compare_list_elementwise(*args):
	try:
		if all(len(args[0]) == len(_arg) for _arg in args[1:]):
			return all(all([element in (item) for element in args[0]]) for item in args[1:])
		else:
			return False
	except TypeError:
		frappe.throw(_("Compare List function takes on list arguments"))

def evaluate_response(answers, response_dict):
	result = {}
	for key in answers:
		try:
			if isinstance(response_dict[key], list):
				is_correct = compare_list_elementwise(response_dict[key], answers[key])
			else:
				is_correct = (response_dict[key] == answers[key])
		except Exception as e:
			is_correct = False
		result[key] = is_correct
	return result

