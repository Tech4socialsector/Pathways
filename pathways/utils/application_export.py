# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Excel export of full applications (Applications list > Export).

Every Application and Candidate field the detail page shows, with the
child tables flattened into numbered columns (Qualification 1 — Degree
Name, ...), screening answers as one column per question and uploaded
files as links. Either one sheet for everything or one sheet per Job
Opening, behind a Summary sheet."""

import datetime
import io
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, get_url, getdate, get_datetime

MODES = ("single", "job_wise", "position_wise")

# Pay is not for committee members (see get_application_detail).
PAY_FIELDS = ("current_salary", "expected_salary")
# Shown as their own columns (screening) or not data at all.
SKIP_APPLICATION_FIELDS = {"naming_series", "candidate", "screening_answers", "documents"}
# Always present, even when empty for every row in a sheet.
CORE_KEYS = {"extra:Position", "extra:Stage", "application_id", "job_opening", "status", "application_date", "cand:full_name", "cand:email", "cand:mobile_number"}

LAYOUT_LABELS = {
	"single": "Single sheet",
	"job_wise": "One sheet per job opening",
	"position_wise": "One sheet per position",
}

MAX_CELL = 32767  # Excel's limit on characters in a cell
SHEET_NAME_BAD = re.compile(r"[\[\]:*?/\\]")
HEADER_FILL = "8B0D25"


def build_workbook(names, mode):
	"""Return (xlsx bytes, number of applications exported)."""
	from openpyxl import Workbook

	wb = Workbook()
	summary = wb.active
	summary.title = _("Summary")
	summary_rows, total = add_application_sheets(wb, names, mode, used_names={summary.title.lower()})
	_write_summary(summary, summary_rows, total, mode)

	buffer = io.BytesIO()
	wb.save(buffer)
	return buffer.getvalue(), total


def add_application_sheets(wb, names, mode, used_names, extra=None, locations=None):
	"""Write the applications into wb: one sheet ("single"), one per job
	opening ("job_wise") or one per position ("position_wise"). Returns
	([(sheet, id, title, count)], total).

	extra: {application: {header: value}} columns placed right after the
	candidate's name (e.g. Position, Stage). locations, when given, is
	filled with {application: (sheet name, row)}."""
	if mode not in MODES:
		frappe.throw(_("Unknown export type."))

	apps = _load_applications(names)
	if not apps:
		frappe.throw(_("None of the selected applications can be exported."))

	ctx = _Context()
	records = [_record(app, ctx) for app in apps]
	if extra:
		for rec in records:
			_insert_extra(rec, extra.get(rec["name"]) or {})

	if mode == "single":
		groups = [(_("All Applications"), None, records)]
	elif mode == "position_wise":
		jobs = {j.name: j.position for j in frappe.get_all("Job Opening", filters={"name": ["in", list({r["job_opening_id"] for r in records})]}, fields=["name", "position"])}
		titles = dict(frappe.get_all("Position", fields=["name", "position_title"], as_list=True))
		by_pos = {}
		for rec in records:
			by_pos.setdefault(jobs.get(rec["job_opening_id"]) or "", []).append(rec)
		groups = sorted(
			((f"{pos} {titles.get(pos) or ''}".strip() if pos else _("No position"), pos or _("No position"), recs) for pos, recs in by_pos.items()),
			key=lambda g: g[0].lower(),
		)
	else:
		by_job = {}
		for rec in records:
			by_job.setdefault(rec["job_opening_id"], []).append(rec)
		groups = sorted(
			((recs[0]["values"]["job_opening"] or job, job, recs) for job, recs in by_job.items()),
			key=lambda g: (g[0] or "").lower(),
		)

	summary_rows = []
	for title, ref, recs in groups:
		sheet_name = _sheet_name(title, used_names)
		_write_sheet(wb.create_sheet(sheet_name), recs)
		if locations is not None:
			for row, rec in enumerate(recs, start=2):
				locations[rec["name"]] = (sheet_name, row)
		summary_rows.append((sheet_name, ref or "", title if ref else _("All job openings"), len(recs)))
	return summary_rows, len(records)


def _insert_extra(rec, extra):
	"""Put extra columns right after the candidate's name."""
	if not extra:
		return
	values, headers = {}, {}
	placed = False
	for key, value in rec["values"].items():
		values[key], headers[key] = value, rec["headers"][key]
		if key == "cand:full_name":
			for header, v in extra.items():
				values[f"extra:{header}"], headers[f"extra:{header}"] = v, header
			placed = True
	if not placed:
		for header, v in extra.items():
			values[f"extra:{header}"], headers[f"extra:{header}"] = v, header
	rec["values"], rec["headers"] = values, headers


def _load_applications(names):
	if isinstance(names, str):
		names = frappe.parse_json(names)
	names = [n for n in (names or []) if isinstance(n, str) and n]
	if not names:
		frappe.throw(_("Select at least one application to export."))
	# get_list, not get_all: only what this user may read (committee scoping).
	readable = set(frappe.get_list("Application", filters={"name": ["in", names]}, pluck="name", limit_page_length=0))
	# Keep the order of the list page; drop duplicates.
	ordered = list(dict.fromkeys(n for n in names if n in readable))
	return [frappe.get_doc("Application", n) for n in ordered]


class _Context:
	"""Per-export caches and the field lists."""

	def __init__(self):
		from pathways.api.application import _data_fields
		from pathways.permissions import has_full_access

		self.show_pay = has_full_access("Application")
		self.candidate_fields = _data_fields("Candidate")
		# _data_fields leaves out Table fields (no_value_fields): add them back
		# in form order.
		data = {df.fieldname for df in _data_fields("Application")}
		self.application_fields = [
			df
			for df in frappe.get_meta("Application").fields
			if (df.fieldname in data or (df.fieldtype == "Table" and not df.hidden))
			and df.fieldname not in SKIP_APPLICATION_FIELDS
			and (self.show_pay or df.fieldname not in PAY_FIELDS)
		]
		self.child_fields = {
			df.fieldname: _data_fields(df.options) for df in self.application_fields if df.fieldtype == "Table"
		}
		self._candidates = {}
		self._titles = {}

	def candidate(self, name):
		if name not in self._candidates:
			fields = [df.fieldname for df in self.candidate_fields]
			self._candidates[name] = frappe.db.get_value("Candidate", name, fields, as_dict=True) or {}
		return self._candidates[name]

	def link_title(self, doctype, name):
		"""Title of a linked record when its ID is a series (Institution
		Master, Job Opening); the ID otherwise."""
		if not name:
			return name
		key = (doctype, name)
		if key not in self._titles:
			meta = frappe.get_meta(doctype)
			title = None
			if meta.title_field and meta.title_field != "name":
				title = frappe.db.get_value(doctype, name, meta.title_field)
			self._titles[key] = title or name
		return self._titles[key]


def _value(df, value, ctx):
	"""A field value as an Excel cell value (or a ('link', url) pair)."""
	if value in (None, ""):
		return None
	if df.fieldtype in ("Attach", "Attach Image"):
		return ("link", get_url(value) if value.startswith("/") else value)
	if df.fieldtype == "Check":
		return _("Yes") if cint(value) else _("No")
	if df.fieldtype == "Link":
		return ctx.link_title(df.options, value)
	if df.fieldtype == "Date":
		return getdate(value)
	if df.fieldtype == "Datetime":
		return get_datetime(value)
	if df.fieldtype in ("Int",):
		return cint(value)
	if df.fieldtype in ("Float", "Currency", "Percent"):
		return flt(value)
	return value


def _record(app, ctx):
	"""One application as an ordered {column key: value} plus the column
	headers for its keys (children and screening vary per application)."""
	values = {}
	headers = {}

	def put(key, header, value):
		values[key] = value
		headers[key] = header

	for df in ctx.application_fields:
		if df.fieldtype != "Table":
			if df.fieldname == "application_id":
				put("application_id", _(df.label), app.application_id)
				# Candidate right after the ID: who it is reads first.
				candidate = ctx.candidate(app.candidate)
				for cdf in ctx.candidate_fields:
					put(f"cand:{cdf.fieldname}", _(cdf.label), _value(cdf, candidate.get(cdf.fieldname), ctx))
			else:
				put(df.fieldname, _(df.label), _value(df, app.get(df.fieldname), ctx))
			continue
		for i, row in enumerate(app.get(df.fieldname) or [], start=1):
			label = _(df.label)
			for cdf in ctx.child_fields[df.fieldname]:
				put(
					f"{df.fieldname}:{i}:{cdf.fieldname}",
					f"{label} {i} — {_(cdf.label)}",
					_value(cdf, row.get(cdf.fieldname), ctx),
				)

	for row in app.get("screening_answers") or []:
		question = (row.question or "").strip()
		if not question:
			continue
		answer = (row.answer or "").strip()
		details = (row.details or "").strip()
		put(f"screening:{question}", question, f"{answer} — {details}" if answer and details else answer or details or None)

	for row in app.get("documents") or []:
		if row.document_type and row.attachment:
			put(f"document:{row.document_type}", f"{_('Document')} — {row.document_type}", _value(_ATTACH, row.attachment, ctx))

	return {"values": values, "headers": headers, "job_opening_id": app.job_opening, "name": app.name}


_ATTACH = frappe._dict(fieldtype="Attach")


def _columns(records):
	"""Union of the records' keys in a stable order: application fields as
	they appear on the form, then each child table's rows in number order,
	then screening questions and documents in first-seen order. Columns
	empty for every record are dropped, except the core ones."""
	order = {}
	headers = {}
	for rec in records:
		for key, header in rec["headers"].items():
			if key not in order:
				order[key] = len(order)
				headers[key] = header

	def sort_key(key):
		kind = key.split(":", 1)[0]
		if kind == "screening":  # before the table check: questions may contain ':'
			return (2, 0, 0, order[key])
		if kind == "document":
			return (3, 0, 0, order[key])
		parts = key.split(":")
		if len(parts) == 3 and parts[1].isdigit():  # child table field
			return (1, _table_position(parts[0], order), int(parts[1]), order[key])
		return (0, 0, 0, order[key])

	def filled(value):
		# A number field the form did not ask for is stored as 0.
		return value not in (None, "") and not (isinstance(value, (int, float)) and value == 0)

	keys = sorted(order, key=sort_key)
	keys = [k for k in keys if k in CORE_KEYS or any(filled(rec["values"].get(k)) for rec in records)]
	return [(k, headers[k]) for k in keys]


def _table_position(table, order):
	# First-seen position of any column of this table: keeps tables in form order.
	return min(v for k, v in order.items() if k.startswith(f"{table}:"))


def _cell_text(value):
	from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

	text = ILLEGAL_CHARACTERS_RE.sub("", str(value))
	return text[:MAX_CELL]


def _write_sheet(ws, records):
	from openpyxl.styles import Alignment, Font, PatternFill
	from openpyxl.utils import get_column_letter

	columns = _columns(records)
	header_font = Font(bold=True, color="FFFFFF")
	header_fill = PatternFill("solid", fgColor=HEADER_FILL)
	link_font = Font(color="0563C1", underline="single")
	widths = []

	for c, (_key, header) in enumerate(columns, start=1):
		cell = ws.cell(row=1, column=c, value=_cell_text(header))
		cell.font = header_font
		cell.fill = header_fill
		cell.alignment = Alignment(vertical="top", wrap_text=True)
		widths.append(min(max(len(header), 10), 40))

	for r, rec in enumerate(records, start=2):
		for c, (key, _header) in enumerate(columns, start=1):
			value = rec["values"].get(key)
			if value is None:
				continue
			cell = ws.cell(row=r, column=c)
			if isinstance(value, tuple) and value[0] == "link":
				cell.value = _cell_text(value[1])
				cell.data_type = "s"
				cell.hyperlink = value[1]
				cell.font = link_font
				shown = 30
			elif isinstance(value, datetime.datetime):
				cell.value = value
				cell.number_format = "DD-MMM-YYYY HH:MM"
				shown = 17
			elif isinstance(value, datetime.date):
				cell.value = value
				cell.number_format = "DD-MMM-YYYY"
				shown = 12
			elif isinstance(value, (int, float)) and not isinstance(value, bool):
				cell.value = value
				shown = len(str(value))
			else:
				cell.value = _cell_text(value)
				# Text typed by candidates, never a formula ("=HYPERLINK(...)").
				cell.data_type = "s"
				shown = max((len(line) for line in cell.value.splitlines()), default=0)
			widths[c - 1] = min(max(widths[c - 1], shown + 2), 60)

	for c, width in enumerate(widths, start=1):
		ws.column_dimensions[get_column_letter(c)].width = width
	ws.row_dimensions[1].height = 32
	# Keep the header and the application ID + candidate name in view.
	ws.freeze_panes = "C2" if len(columns) > 2 else "A2"
	if columns:
		ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(records) + 1}"


def _write_summary(ws, rows, total, mode):
	from openpyxl.styles import Font, PatternFill
	from openpyxl.worksheet.hyperlink import Hyperlink

	ws.append([_("Applications Export")])
	ws["A1"].font = Font(bold=True, size=14)
	ws.append([_("Exported On"), frappe.utils.now_datetime()])
	ws["B2"].number_format = "DD-MMM-YYYY HH:MM"
	ws.append([_("Exported By"), frappe.utils.get_fullname(frappe.session.user)])
	ws.append([_("Layout"), LAYOUT_LABELS.get(mode, mode)])
	ws.append([_("Total Applications"), total])
	ws.append([])
	ws.append([_("Sheet"), _("Position") if mode == "position_wise" else _("Job Opening ID"), _("Position / Job Opening"), _("Applications")])
	for cell in ws[ws.max_row]:
		cell.font = Font(bold=True, color="FFFFFF")
		cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
	for sheet_name, job, title, count in rows:
		ws.append([sheet_name, job, _cell_text(title), count])
		link = ws.cell(row=ws.max_row, column=1)
		escaped = sheet_name.replace("'", "''")
		link.hyperlink = Hyperlink(ref=link.coordinate, location=f"'{escaped}'!A1")
		link.font = Font(color="0563C1", underline="single")
		ws.cell(row=ws.max_row, column=3).data_type = "s"
	for col, width in zip("ABCD", (34, 26, 60, 14)):
		ws.column_dimensions[col].width = width


def _sheet_name(title, used):
	"""Excel sheet names: at most 31 characters, none of []:*?/\\, not
	starting or ending with an apostrophe, unique ignoring case."""
	base = SHEET_NAME_BAD.sub("-", title or "").strip().strip("'").strip() or _("Sheet")
	base = base[:31].rstrip()
	name, n = base, 2
	while name.lower() in used:
		suffix = f" ({n})"
		name = base[: 31 - len(suffix)].rstrip() + suffix
		n += 1
	used.add(name.lower())
	return name
