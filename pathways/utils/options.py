# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Dropdown choices are listed A-Z, so a newly added option falls into its
place instead of landing at the end of the list."""

import re

import frappe

# Catch-all choices stay at the end of a list, in this order.
LAST = ("other", "others", "none", "not applicable", "prefer not to say")


def _natural(text):
	# "Level 2" before "Level 10"; case and spacing ignored.
	return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", " ".join(str(text).lower().split()))]


def sort_options(options):
	"""Options A-Z (natural, case-insensitive). A blank option stays first,
	catch-alls such as "Other" or "Prefer not to say" stay last."""
	options = list(options or [])
	blank = [o for o in options if not (o or "").strip()]
	tail = sorted((o for o in options if (o or "").strip().lower() in LAST), key=lambda o: LAST.index(o.strip().lower()))
	rest = sorted((o for o in options if (o or "").strip() and (o or "").strip().lower() not in LAST), key=_natural)
	return [*blank[:1], *rest, *tail]


def select_options(doctype, fieldname):
	"""A Select field's options (without the blank one), A-Z."""
	return sort_options(o for o in (frappe.get_meta(doctype).get_field(fieldname).options or "").split("\n") if o)
