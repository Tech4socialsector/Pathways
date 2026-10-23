# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Department folders for job documents (workflow step 7).

Every job gets a folder in Frappe's File manager,

	Home/Pathways/<Department>/<Job title - Job ID>

so the JD, notification, office orders and anything else attached to the
job sit together under its department, the way the recruitment team keeps
its shared drive. Creating it is idempotent: an existing folder is reused,
and the job only remembers its path (Job Opening.files_folder)."""

import re

import frappe

ROOT = "Home/Pathways"


def _clean(label):
	# "/" separates folders in a File name; keep everything else readable.
	label = re.sub(r"[\\/]+", "-", (label or "").strip())
	return re.sub(r"\s+", " ", label)[:120] or "Unassigned"


def ensure_folder(name, parent):
	"""Folder `name` under `parent` ("Home/..."), created when missing.
	Returns its File name (the full path)."""
	path = f"{parent}/{name}"
	if not frappe.db.exists("File", {"name": path, "is_folder": 1}):
		existing = frappe.db.get_value("File", {"is_folder": 1, "folder": parent, "file_name": name}, "name")
		if existing:
			return existing
		frappe.get_doc({"doctype": "File", "file_name": name, "is_folder": 1, "folder": parent}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)
	return path


def job_folder_path(job):
	return f"{ROOT}/{_clean(job.department)}/{_clean(f'{job.job_title} - {job.name}')}"


def ensure_job_folder(job):
	"""Create the job's folder (and its parents), move the files attached
	to the job into it, and store the path on the job. Safe to call again."""
	if isinstance(job, str):
		job = frappe.get_doc("Job Opening", job)
	if not job.name or not job.job_title:
		return None
	ensure_folder("Pathways", "Home")
	department = ensure_folder(_clean(job.department), ROOT)
	folder = ensure_folder(_clean(f"{job.job_title} - {job.name}"), department)

	# Files uploaded on the job (JD, notification and corrigendum PDFs) go
	# into its folder; files elsewhere are left where they are.
	for name in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Job Opening", "attached_to_name": job.name, "is_folder": 0, "folder": ["!=", folder]},
		pluck="name",
	):
		frappe.db.set_value("File", name, "folder", folder, update_modified=False)

	if job.get("files_folder") != folder:
		job.db_set("files_folder", folder, update_modified=False)
	return folder
