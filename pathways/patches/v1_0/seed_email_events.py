# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Recruitment Email Rules and their Email Templates (Email Setup page)."""

from pathways.utils.email_events import ensure_email_events


def execute():
	ensure_email_events()
