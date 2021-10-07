<!--

Some key notes before you open a PR:

 1. Select which branch should this PR be merged in?
 2. PR name follows [convention](http://karma-runner.github.io/4.0/dev/git-commit-msg.html)
 3. All tests pass locally, UI and Unit tests
 4. All business logic and validations must be on the server-side
 5. Update necessary Documentation
 6. Put `closes #XXXX` in your comment to auto-close the issue that your PR fixes


Also, if you're new here

- Documentation Guidelines => https://github.com/frappe/erpnext/wiki/Updating-Documentation

- Contribution Guide => https://github.com/frappe/erpnext/blob/develop/.github/CONTRIBUTING.md

- Pull Request Checklist => https://github.com/frappe/erpnext/wiki/Pull-Request-Checklist

-->

**Note:**
> Please write PR description for functional users too 🙏🙏🙏. Select your template accordingly.

<!-- Template for Fixes -->
<h2>Template for fixes.</h2>
TODO:

- [x] Fixes
- [x] Patches(If required)
- [ ] Test Cases(If required)

...

<h3>Traceback/Bug Report (Mandatory):</h3>  
This is one line explanation for my bug report.

Screenshots/GIFs to explain (if required)

```
This is Traceback:
2021-10-06T10:52:53.6376705Z     self._validate_mandatory()
2021-10-06T10:52:53.6377674Z   File "/home/runner/frappe-bench/apps/frappe/frappe/model/document.py", line 751, in _validate_mandatory
2021-10-06T10:52:53.6378375Z     name=self.name))
2021-10-06T10:52:53.6379263Z frappe.exceptions.MandatoryError: [Task, TASK-2021-00010]: projects

```

<h3>Steps to replicate (Mandatory):</h3> 

* Step 1
* Step 2
   * Step 2.1
* Step 3

...

<h3>Expected Behaviour/Fixes (Mandatory):</h3> 
This is the behaviour after fixes.

Ex: This pull request ensures that on clicking the Select all button, it will select all items.


<!-- Template for Features -->
<h2>Template for Fetures.</h2>

TODO:(Mandatory)
- [x] Development.
- [x] Test cases.
- [ ] Documentation (If required). 

...

<h3>Description (Mandatory):</h3>
This is one line description.

<h3>Settings(Mandatory If you have any):</h3>
This is one line introduction.

Screenshots/GIFs (Mandatory)

<h3>Masters Document Type (Mandatory, If you have any):</h3>

<h4>DocType 1:</h4>
This is one line introduction(If required).

Screenshots/GIFs (Mandatory)

...

<h3>Transactional Document Type (Mandatory):</h3>

<h4>DocType 1:</h4>
This is one line introduction (If required).

Screenshots/GIFs (Mandatory)

...

<h3>Section 1 (If Required):</h3>
This is one line introduction and you add another section to showcase other developments like reports, dashboards, etc.

Screenshots/GIFs (Mandatory)

...


<h3>Workflow (Mandatory):</h3>

- Step 1
- Step 2
    - Step 2.1
    - Step 2.2
- Step 3
...

<h3>Validation (Optional):</h3>
- Validation 1
- Validation 2

...
