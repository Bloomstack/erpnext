from six import string_types

def get_abbr(txt, max_length=2):
	"""
		Extract abbreviation from the given string as:
			- Single-word strings abbreviate to the letters of the string, upto the max length
			- Multi-word strings abbreviate to the initials of each word, upto the max length

	Args:
		txt (str): The string to abbreviate
		max_length (int, optional): The max length of the abbreviation. Defaults to 2.

	Returns:
		str: The abbreviated string, in uppercase
	"""

	if not txt:
		return

	if not isinstance(txt, string_types):
		try:
			txt = str(txt)
		except:
			return

	abbr = ""
	words = txt.split(" ")

	if len(words) > 1:
		for word in words:
			if len(abbr) >= max_length:
				break

			if word.strip():
				abbr += word.strip()[0]
	else:
		abbr = txt[:max_length]

	abbr = abbr.upper()
	return abbr

def retry(fn, retries=3, on_result=None, on_exception=None):
	"""Retries the provided callable a certain number of times on exceptions
	or if on_result predicate fails.

	Args:
		fn (function): Function to execute and retry
		retries (int, optional): Number of times to retry fn. Defaults to 3.
		on_result ([type], optional): Predicate used to test fn's result. Return true to stop retries. Defaults to None.
		on_exception ([type], optional): Predicate used to test fn's exception. Return true to stop retries. Defaults to None.
	"""
	last_exception = None
	for i in range(retries):
		try:
			result = fn(i)
			if on_result:
				result = on_result(result, i)
				if result:
					return result
				else:
					continue
			return result
		except Exception as ex:
			if on_exception:
				ex = on_exception(ex, i)
				if ex:
					return ex

			last_exception = ex
			continue
		
	return last_exception
