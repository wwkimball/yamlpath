# Contributing to yamlpath

Contents:

1. [Introduction](#introduction)
2. [Issues](#issues)
   1. [Bug Reports](#bug-reports)
   2. [Feature Requests](#feature-requests)
3. [Code](#code)
   1. [Unit Testing](#unit-testing)
4. [Thank You](#thank-you)

## Introduction

Contributions are welcome!  This Python project is a [publicly-accessible package](https://pypi.org/project/yamlpath/), so high-quality
contributions are the foremost expectation.  Whether you wish to [report an issue](#issues) or [contribute code](#code) for a bug-fix or
new feature, you have found the right place.

## Issues

Please report issues via [GitHub's Issues mechanism](https://github.com/wwkimball/yamlpath/issues).  Both bug reports and new feature
requests are welcome.

### Bug Reports

When reporting a defect, you must include *all* of the following information in your issue report:

1. Operating System and its version on the machine(s) exhibiting the unfavorable outcome.
2. Version of Python in use at the time of the issue.
3. Precise version of yamlpath installed.
4. Precise version of ruamel.yaml installed.
5. Minimum sample of YAML (or compatible) data necessary to trigger the issue.
6. Complete steps to reproduce the issue when triggered via:
   1. Command-Line Tools (yaml-get, yaml-set, or eyaml-rotate-keys):  Precise command-line arguments which trigger the defect.
   2. Libraries (yamlpath.*):  Minimum amount of code necessary to trigger the defect.
7. Expected outcome.
8. Actual outcome.

### Feature Requests

When submitting a Feature Request as an Issue, please prefix the Title of your issue report with the term, "FEATURE REQUEST".  Bug Reports
usually take priority over Feature Requests, so this prefix will help sort through Issue reports.  The body of your request should include
details of what you'd like to see this project do.  If possible, include minimal examples of the data and the outcome you want.

## Code

All code contributions must be submitted via Pull Requests against an appropriate Branch of this project.  The "development" branch is a
suitable PR target for most contributions.  When possible, be sure to reference the Issue number in your source Branch name, like:

* feature/123
* bugfix/456

If an Issue doesn't exist for the contribution you wish to make, please consider creating one along with your PR.  Include the Issue
number in the comments of your PR, like:  "Adds feature #123" or "Fixes #456".

### Unit Testing

Every code contribution must include `pytest` unit tests.  Any contributions which _reduce_ the code coverage of the unit testing suite
will be blocked until the missing tests are added.  Any contributins which break existing unit tests *must* include updated unit tests
along with documentation explaining why the test(s) had to change.  Such documentation must be verbose and rational.

## Thank You

For any of you willing to contribute to this project, you have my most sincere appreciation!  Unless you specifically object, I will
include your identity along with a note about your contribution(s) in the [CHANGES](CHANGES) file.
