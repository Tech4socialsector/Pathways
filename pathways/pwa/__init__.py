# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Installable app (PWA) for the Pathways SPA at /pathways.

Two root-level files, served by PWAPage (hooks.page_renderer):

	/pathways.webmanifest  the web app manifest, named and coloured from
	                       Pathways Settings > Appearance
	/pathways-sw.js        the service worker (service-worker.js beside this file)

Why not under /assets like the Vite build: a service worker only controls
pages at or below its own URL, so one at /assets/pathways/... could never
control /pathways. Served from the site root it can, and the SPA registers
it with scope "/pathways" (frontend/src/utils/pwa.js). Neither path matches
the "/pathways/<path:app_path>" route rule, so they reach this renderer.
"""

import re
from pathlib import Path

import frappe
from frappe.utils import get_url
from frappe.website.page_renderers.base_renderer import BaseRenderer

MANIFEST_PATH = "pathways.webmanifest"
SW_PATH = "pathways-sw.js"
SW_FILE = Path(__file__).with_name("service-worker.js")

APP_URL = "/pathways"
ICON_DIR = "/assets/pathways/pwa"
DEFAULT_NAME = "Pathways"
DEFAULT_COLOR = "#920C24"


def _appearance():
	try:
		doc = frappe.get_cached_doc("Pathways Settings")
		return doc.get("app_name"), doc.get("brand_color")
	except Exception:
		# Never break the manifest over settings (e.g. during install).
		return None, None


def build_manifest():
	name, color = _appearance()
	name = (name or "").strip() or DEFAULT_NAME
	color = color if re.fullmatch(r"#[0-9a-fA-F]{6}", color or "") else DEFAULT_COLOR
	return {
		"id": APP_URL,
		"name": name,
		"short_name": name[:12],
		"description": "Recruitment and onboarding at NLSIU",
		"start_url": APP_URL,
		"scope": APP_URL,
		"display": "standalone",
		"orientation": "any",
		"background_color": "#FFFFFF",
		"theme_color": color,
		"categories": ["business", "productivity"],
		# Lets the page ask whether it is already installed
		# (navigator.getInstalledRelatedApps), so the install popup can stay away.
		"related_applications": [{"platform": "webapp", "url": get_url(f"/{MANIFEST_PATH}")}],
		"icons": [
			{"src": f"{ICON_DIR}/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
			{"src": f"{ICON_DIR}/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
			{"src": f"{ICON_DIR}/maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
			{"src": f"{ICON_DIR}/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
		],
	}


class PWAPage(BaseRenderer):
	def can_render(self):
		return self.path in (MANIFEST_PATH, SW_PATH)

	def render(self):
		# Mimetype comes from the extension (frappe.website.utils.set_content_type):
		# application/manifest+json and text/javascript.
		if self.path == SW_PATH:
			# no-cache: the browser revalidates the worker on every visit, so a
			# deploy that changes it is picked up straight away.
			return self.build_response(
				SW_FILE.read_text(), headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": APP_URL}
			)
		return self.build_response(
			frappe.as_json(build_manifest(), indent=None), headers={"Cache-Control": "public, max-age=600"}
		)
