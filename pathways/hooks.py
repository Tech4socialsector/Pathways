app_name = "pathways"
app_title = "Pathways"
app_publisher = "NLSIU"
app_description = "NLSIU Recruitment Management"
app_email = "admin@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pathways",
# 		"logo": "/assets/pathways/logo.png",
# 		"title": "Pathways",
# 		"route": "/pathways",
# 		"has_permission": "pathways.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pathways/css/pathways.css"
# app_include_js = "/assets/pathways/js/pathways.js"

# include js, css files in header of web template
# web_include_css = "/assets/pathways/css/pathways.css"
# web_include_js = "/assets/pathways/js/pathways.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pathways/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pathways/public/icons.svg"

# Website Route Rules
# --------------------
# Serves the Vue SPA for every /pathways/* path from the www/pathways.py
# page, matching the standard Frappe pattern used by CRM/Helpdesk/HRMS.

website_route_rules = [
	{"from_route": "/pathways/<path:app_path>", "to_route": "pathways"},
]

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pathways.utils.jinja_methods",
# 	"filters": "pathways.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "pathways.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pathways.uninstall.before_uninstall"
# after_uninstall = "pathways.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pathways.utils.before_app_install"
# after_app_install = "pathways.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pathways.utils.before_app_uninstall"
# after_app_uninstall = "pathways.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "pathways.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pathways.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["pathways.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Application": "pathways.permissions.get_application_permission_query_conditions",
	"Interview": "pathways.permissions.get_interview_permission_query_conditions",
	"Document Collection": "pathways.permissions.get_document_collection_permission_query_conditions",
	"Offer Appointment Order": "pathways.permissions.get_offer_permission_query_conditions",
	"Joining": "pathways.permissions.get_joining_permission_query_conditions",
}

has_permission = {
	"Application": "pathways.permissions.has_application_permission",
	"Interview": "pathways.permissions.has_interview_permission",
	"Document Collection": "pathways.permissions.has_document_collection_permission",
	"Offer Appointment Order": "pathways.permissions.has_offer_permission",
	"Joining": "pathways.permissions.has_joining_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Application": {
		"on_update": "pathways.utils.audit.log_application_status_change",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"pathways.tasks.daily",
	],
}

# Testing
# -------

# before_tests = "pathways.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "pathways.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pathways.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pathways.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pathways.utils.before_request"]
# after_request = ["pathways.utils.after_request"]

# Job Events
# ----------
# before_job = ["pathways.utils.before_job"]
# after_job = ["pathways.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pathways.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

