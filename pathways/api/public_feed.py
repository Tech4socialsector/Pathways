# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Public job feeds (workflow step 3: website and job boards).

Communications publishes each advertisement on the NLSIU website, LinkedIn
and Indeed. Instead of retyping every job, those sites read two guest,
read-only feeds of the jobs that are open right now:

	/jobs-feed.xml   Indeed's XML job feed (<source><job>...</job></source>)
	/jobs-feed.json  JSON for the NLSIU website

(also as API methods, indeed_feed and get_jobs_feed). Only Advertised jobs
whose deadline has not passed are listed, and only fields already shown on
the public posting page (pathways.api.application.PUBLIC_JOB_FIELDS) plus
the JD and the official notification — never anything internal."""

import xml.etree.ElementTree as ET
from email.utils import format_datetime as rfc2822

import frappe
from frappe.utils import get_datetime, get_url, now_datetime
from frappe.website.page_renderers.base_renderer import BaseRenderer

from pathways.api.application import PUBLIC_JOB_FIELDS
from pathways.pathways.doctype.job_opening.job_opening import get_advertisement_url

# The organisation behind every listing. A site may override these in
# site_config.json (pathways_feed_company, _city, _state, _country, _postalcode).
FEED_DEFAULTS = {
	"company": "National Law School of India University",
	"city": "Bengaluru",
	"state": "Karnataka",
	"country": "IN",
	"postalcode": "560072",
}

# Job Opening > Employment Type -> Indeed <jobtype>.
INDEED_JOB_TYPES = {
	"Permanent": "fulltime",
	"Contract": "contract",
	"Consultant": "contract",
	"Grant-funded": "temporary",
}

FEED_ROUTES = {"jobs-feed.xml": "xml", "jobs-feed.json": "json"}


def _feed_setting(key):
	return frappe.conf.get(f"pathways_feed_{key}") or FEED_DEFAULTS[key]


def open_jobs():
	"""Advertised jobs still taking applications, newest first, as public
	dicts (no permission check: these are exactly what the public job board
	shows)."""
	fields = [*PUBLIC_JOB_FIELDS, "jd_text", "jd_attachment", "website_published_on", "creation", "modified"]
	jobs = frappe.get_all(
		"Job Opening", filters={"status": "Advertised"}, fields=fields, order_by="creation desc", ignore_permissions=True
	)
	now = now_datetime()
	jobs = [j for j in jobs if not j.application_deadline or get_datetime(j.application_deadline) > now]
	notices = {}
	if jobs:
		for n in frappe.get_all(
			"Recruitment Notification",
			filters={"job_opening": ["in", [j.name for j in jobs]]},
			fields=["job_opening", "notification_number", "notification_url", "notification_attachment"],
			order_by="creation asc",
			ignore_permissions=True,
		):
			notices[n.job_opening] = n
	for job in jobs:
		job.url = get_advertisement_url(job.name)
		job.posted_on = job.website_published_on or job.application_start or job.creation
		job.notice = notices.get(job.name)
	return jobs


def _absolute(url):
	if not url:
		return None
	return url if url.startswith("http") else get_url(url)


def build_indeed_xml(jobs=None):
	"""Indeed's standard XML feed. ElementTree escapes the text, so the JD's
	HTML arrives intact as text, which Indeed accepts."""
	jobs = open_jobs() if jobs is None else jobs
	source = ET.Element("source")
	ET.SubElement(source, "publisher").text = _feed_setting("company")
	ET.SubElement(source, "publisherurl").text = get_url()
	ET.SubElement(source, "lastBuildDate").text = rfc2822(now_datetime())
	for job in jobs:
		node = ET.SubElement(source, "job")
		values = {
			"title": job.job_title,
			"date": rfc2822(get_datetime(job.posted_on)),
			"referencenumber": job.name,
			"url": job.url,
			"company": _feed_setting("company"),
			"city": _feed_setting("city"),
			"state": _feed_setting("state"),
			"country": _feed_setting("country"),
			"postalcode": _feed_setting("postalcode"),
			"description": job.jd_text or job.job_title,
			"jobtype": INDEED_JOB_TYPES.get(job.employment_type, "fulltime"),
			"category": job.track,
			"expirationdate": rfc2822(get_datetime(job.application_deadline)) if job.application_deadline else None,
		}
		for tag, value in values.items():
			if value:
				ET.SubElement(node, tag).text = str(value)
	return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(source, encoding="unicode")


def build_json_feed(jobs=None):
	jobs = open_jobs() if jobs is None else jobs
	out = []
	for job in jobs:
		notice = job.notice or {}
		out.append(
			{
				"id": job.name,
				"title": job.job_title,
				"department": job.department,
				"track": job.track,
				"designation": job.designation,
				"vacancies": job.vacancies,
				"employment_type": job.employment_type,
				"tenure": job.tenure_description,
				"pay_level": job.pay_level,
				"application_start": str(job.application_start) if job.application_start else None,
				"application_deadline": str(job.application_deadline) if job.application_deadline else None,
				"posted_on": str(job.posted_on) if job.posted_on else None,
				"url": job.url,
				"jd_url": _absolute(job.jd_attachment),
				"description_html": job.jd_text,
				"notification_number": notice.get("notification_number"),
				"notification_url": notice.get("notification_url") or _absolute(notice.get("notification_attachment")),
			}
		)
	return {"organisation": _feed_setting("company"), "generated_on": str(now_datetime()), "jobs": out}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_jobs_feed():
	"""JSON feed for the NLSIU website."""
	return build_json_feed()


@frappe.whitelist(allow_guest=True, methods=["GET"])
def indeed_feed():
	"""Indeed XML feed as an API method (the same as /jobs-feed.xml)."""
	from werkzeug.wrappers import Response

	return Response(build_indeed_xml(), mimetype="application/xml", headers={"Cache-Control": "public, max-age=900"})


class JobFeedPage(BaseRenderer):
	"""Serves /jobs-feed.xml and /jobs-feed.json (hooks.page_renderer), so the
	feeds have short, stable URLs that do not depend on the API path."""

	def can_render(self):
		return self.path in FEED_ROUTES

	def render(self):
		if FEED_ROUTES[self.path] == "xml":
			data = build_indeed_xml()
		else:
			data = frappe.as_json(build_json_feed())
		# Mimetype comes from the path's extension (frappe.website.utils.set_content_type).
		return self.build_response(data, headers={"Cache-Control": "public, max-age=900"})
