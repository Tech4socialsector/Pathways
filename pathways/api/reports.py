# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Reports page: application charts and their Excel export.

Aggregates only (counts per group), behind the same gate as the
dashboard pipeline numbers. One function, _charts, builds every chart so
the page, the CSV and the Excel file always agree.

Each chart: {key, title, subtitle, kind, total, table, ...data}, where
kind is one of
  pie / donut   part-to-whole           slices: [{label, value, color, detail?}]
  bar           ranked, horizontal      slices
  funnel        stages reached          slices (shares are of the first stage)
  column        ordered bins            slices
  stacked       groups split by stage   categories, series: [{label, color, values}]
  line          applications over time  points: [{label, value}]
and table = {header, rows, percent: [column indexes holding fractions]}
is the same numbers as a grid (CSV, Excel)."""

import datetime
import io

import frappe
from frappe import _
from frappe.utils import add_days, add_months, date_diff, get_datetime, get_first_day, getdate, now_datetime, today

from pathways.api.dashboard import FUNNEL_STAGES, require_pipeline_access

# Charts are themed from the brand colour (Pathways Settings > Appearance,
# NLS maroon by default), in the same shades the app uses (theme.js).
DEFAULT_BRAND = "#920C24"
BRAND_SHADES = {300: 0.55, 400: 0.35, 500: 0.18, 600: 0.08, 700: 0, 900: -0.36}
# After the brand, the other categorical hues in a fixed order. With the
# maroon lead this order is validated colour-blind safe for neighbours,
# including a pie's last-to-first wrap.
OTHER_HUES = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#eda100", "#008300", "#e87ba4"]
# Fills a slot only when a hue above is dropped for looking like the brand.
RESERVE_HUES = ["#e34948"]
NEUTRAL = "#898781"  # "Other" / "Not specified"
STATUS_GOOD, STATUS_WARNING, STATUS_CRITICAL = "#0ca30c", "#fab219", "#d03b3b"

# Application statuses grouped into eight stages (one colour each, the
# same in every chart).
STAGES = [
	("Screening", ["Submitted", "Under Review"]),
	("Shortlisted", ["Shortlisted"]),
	("Interview", ["Interview Scheduled", "Interview Completed"]),
	("Selected", ["Selected"]),
	("Offer", ["Offer Extended", "Offer Accepted", "Offer Declined"]),
	("Onboarding", ["Documents Pending", "Documents Verified"]),
	("Joined", ["Joined"]),
	("Closed", ["Not Selected", "Withdrawn"]),
]
STAGE_OF = {status: stage for stage, statuses in STAGES for status in statuses}
# No longer moving: left out of the ageing chart.
FINISHED = {"Joined", "Not Selected", "Withdrawn", "Offer Declined"}
AGE_BANDS = [(0, 7, "0–7 days"), (8, 14, "8–14 days"), (15, 30, "15–30 days"), (31, 60, "31–60 days"), (61, None, "Over 60 days")]


def _hex(rgb):
	return "#{:02x}{:02x}{:02x}".format(*rgb)


def _brand_scale(color):
	"""Shades of the brand colour: 700 is the colour itself, lighter ones
	blend toward white, darker toward black (as theme.js brandScale)."""
	value = (color or "").strip().lstrip("#")
	if len(value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in value):
		value = DEFAULT_BRAND.lstrip("#")
	base = [int(value[i : i + 2], 16) for i in (0, 2, 4)]
	scale = {}
	for shade, amount in BRAND_SHADES.items():
		target = 255 if amount >= 0 else 0
		scale[shade] = _hex([round(c + (target - c) * abs(amount)) for c in base])
	return scale


def _oklab(color):
	def linear(c):
		c /= 255
		return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

	r, g, b = (linear(int(color[i : i + 2], 16)) for i in (1, 3, 5))
	l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
	m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
	s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
	return (
		0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
		1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
		0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
	)


def _distance(a, b):
	"""Perceptual colour difference (OKLab x 100); under 15 reads as the same colour."""
	return 100 * sum((x - y) ** 2 for x, y in zip(_oklab(a), _oklab(b))) ** 0.5


def _theme():
	"""{primary, ramp, palette} for the configured brand colour.

	palette[0] is the brand (shade 600: shade 700 is too dark to sit among
	the other hues); a hue that looks too like it is dropped, so no two
	slots look alike if the brand is changed from maroon."""
	scale = _brand_scale(frappe.get_cached_doc("Pathways Settings").get("brand_color"))
	lead = scale[600]
	return frappe._dict(
		primary=scale[700],
		ramp=[scale[s] for s in (300, 400, 500, 700, 900)],
		palette=[lead] + [c for c in OTHER_HUES + RESERVE_HUES if _distance(c, lead) >= 15][: len(OTHER_HUES)],
	)


def _filters(track=None, job_opening=None, from_date=None, to_date=None):
	"""Application filters; every given filter applies (AND)."""
	filters = {}
	jobs = None
	if track:
		jobs = set(frappe.get_all("Job Opening", filters={"track": track}, pluck="name"))
	if job_opening:
		jobs = {job_opening} if jobs is None else jobs & {job_opening}
	if jobs is not None:
		# An empty list would mean "no filter" to frappe: match nothing instead.
		filters["job_opening"] = ["in", list(jobs) or [""]]

	start = getdate(from_date) if from_date else None
	end = getdate(to_date) if to_date else None
	if start and end and start > end:
		frappe.throw(_("The From date must be on or before the To date."))
	if start and end:
		filters["application_date"] = ["between", [start, end]]
	elif start:
		filters["application_date"] = [">=", start]
	elif end:
		filters["application_date"] = ["<=", end]
	return filters


def _job_filters(track=None, job_opening=None):
	f = {}
	if track:
		f["track"] = track
	if job_opening:
		f["name"] = job_opening
	return f


def _slices(counts, palette, order=None):
	"""[{label, value, color}] for a pie.

	With a fixed `order` of at most eight entities, each keeps its slot
	colour whatever the filters (colour follows the entity). Otherwise the
	largest groups take the slots in rank order and the rest fold into
	"Other (n)"."""
	counts = {k: v for k, v in counts.items() if v}
	unspecified = counts.pop(None, 0)
	if order is not None and len(order) <= len(palette):
		slices = [{"label": key, "value": counts.pop(key, 0), "color": palette[i]} for i, key in enumerate(order)]
		# Values outside the known list (e.g. a renamed master).
		slices += [{"label": k, "value": v, "color": NEUTRAL} for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
	else:
		ranked = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
		keep = ranked if len(ranked) <= len(palette) else ranked[: len(palette) - 1]
		rest = ranked[len(keep) :]
		slices = [{"label": key, "value": value, "color": palette[i]} for i, (key, value) in enumerate(keep)]
		if rest:
			slices.append(
				{
					"label": _("Other ({0})").format(len(rest)),
					"value": sum(v for _k, v in rest),
					"color": NEUTRAL,
					"detail": [{"label": k, "value": v} for k, v in rest],
				}
			)
	if unspecified:
		slices.append({"label": _("Not specified"), "value": unspecified, "color": NEUTRAL})
	return slices


def _count(rows, key):
	counts = {}
	for row in rows:
		value = key(row) or None
		counts[value] = counts.get(value, 0) + 1
	return counts


def _select_options(doctype, fieldname):
	return [o for o in (frappe.get_meta(doctype).get_field(fieldname).options or "").split("\n") if o]


def _slice_chart(key, kind, title, subtitle, slices, first_column):
	"""A chart drawn from slices, with its table."""
	total = sum(s["value"] for s in slices)
	if kind == "funnel":
		# Shares are of the first stage (every application), not of the sum.
		total = slices[0]["value"] if slices else 0
		header = [first_column, _("Applications"), _("% of Applied")]
	else:
		header = [first_column, _("Applications"), _("Share")]
	rows = [[s["label"], s["value"], (s["value"] / total) if total else 0] for s in slices]
	return {
		"key": key,
		"kind": kind,
		"title": title,
		"subtitle": subtitle,
		"slices": slices,
		"total": total,
		"table": {"header": header, "rows": rows, "percent": [2]},
	}


def _timeline(apps, from_date, to_date):
	"""Applications per day, week (from Monday) or month, gaps filled with 0."""
	dates = [getdate(a.application_date or get_datetime(a.creation)) for a in apps]
	if not dates:
		return [], "day"
	start = getdate(from_date) if from_date else min(dates)
	end = getdate(to_date) if to_date else max(dates)
	span = date_diff(end, start)
	if span <= 45:
		unit, bucket = "day", lambda d: d
	elif span <= 7 * 30:
		unit, bucket = "week", lambda d: d - datetime.timedelta(days=d.weekday())
	else:
		unit, bucket = "month", lambda d: get_first_day(d)

	counts = {}
	for d in dates:
		counts[bucket(d)] = counts.get(bucket(d), 0) + 1
	points = []
	current, last = bucket(start), bucket(end)
	while current <= last:
		label = current.strftime("%b %Y") if unit == "month" else current.strftime("%d %b %Y")
		points.append({"label": label, "date": current.isoformat(), "value": counts.get(current, 0)})
		current = add_months(current, 1) if unit == "month" else add_days(current, 7 if unit == "week" else 1)
	return points, unit


def _charts(filters, job_filters, from_date=None, to_date=None):
	theme = _theme()
	# One colour per stage, the same in every chart.
	stage_color = {stage: theme.palette[i] if i < len(theme.palette) else NEUTRAL for i, (stage, _s) in enumerate(STAGES)}
	apps = frappe.get_all(
		"Application",
		filters=filters,
		fields=["name", "status", "eligibility_status", "job_opening", "source", "candidate", "application_date", "creation"],
		limit_page_length=0,
	)
	jobs = {
		j.name: j
		for j in frappe.get_all("Job Opening", filters=job_filters, fields=["name", "job_title", "track"], order_by="creation desc")
	}
	missing = {a.job_opening for a in apps} - set(jobs)
	if missing:
		for j in frappe.get_all("Job Opening", filters={"name": ["in", list(missing)]}, fields=["name", "job_title", "track"]):
			jobs[j.name] = j
	candidates = {}
	if apps:
		candidates = {
			c.name: c
			for c in frappe.get_all(
				"Candidate", filters={"name": ["in", list({a.candidate for a in apps})]}, fields=["name", "gender", "category"]
			)
		}
	track_of = lambda a: jobs.get(a.job_opening, {}).get("track")  # noqa: E731
	charts = []

	# 1. Applications over time
	points, unit = _timeline(apps, from_date, to_date)
	period = {"day": _("Date"), "week": _("Week Starting"), "month": _("Month")}[unit]
	charts.append(
		{
			"key": "timeline",
			"kind": "line",
			"color": theme.primary,
			"title": _("Applications Over Time"),
			"subtitle": _("Applications received per {0}.").format(_(unit)),
			"points": points,
			"unit": unit,
			"total": sum(p["value"] for p in points),
			"table": {"header": [period, _("Applications")], "rows": [[p["label"], p["value"]] for p in points], "percent": []},
		}
	)

	# 2. Funnel: applications that REACHED each stage (dashboard's definition).
	by_status = _count(apps, lambda a: a.status)
	funnel = [
		{"label": _(label), "value": sum(by_status.get(s, 0) for s in statuses), "color": theme.ramp[min(i, len(theme.ramp) - 1)]}
		for i, (label, statuses) in enumerate(FUNNEL_STAGES)
	]
	charts.append(
		_slice_chart(
			"funnel", "funnel", _("Recruitment Funnel"), _("Applications that reached each stage, as a share of all applied."),
			funnel, _("Stage"),
		)
	)

	# 3. Current status, grouped into stages; the tooltip lists the statuses inside.
	stage_slices = []
	for stage, statuses in STAGES:
		detail = [{"label": s, "value": by_status[s]} for s in statuses if by_status.get(s)]
		stage_slices.append(
			{
				"label": _(stage),
				"value": sum(d["value"] for d in detail),
				"color": stage_color[stage],
				"detail": detail if len(statuses) > 1 else [],
			}
		)
	other = {s: n for s, n in by_status.items() if s not in STAGE_OF}
	if other:
		stage_slices.append(
			{
				"label": _("Other"),
				"value": sum(other.values()),
				"color": NEUTRAL,
				"detail": [{"label": s or _("Not specified"), "value": n} for s, n in other.items()],
			}
		)
	charts.append(
		_slice_chart("status", "donut", _("Application Status"), _("Where applications stand right now."), stage_slices, _("Stage"))
	)

	# 4. Each track split by stage.
	tracks = frappe.get_all("Recruitment Track", pluck="name", order_by="creation asc")
	per_track = {}
	for a in apps:
		counts = per_track.setdefault(track_of(a) or _("Not specified"), {})
		stage = STAGE_OF.get(a.status, "Other")
		counts[stage] = counts.get(stage, 0) + 1
	categories = [t for t in tracks if t in per_track] + sorted(t for t in per_track if t not in tracks)
	stage_names = [s for s, _x in STAGES] + (["Other"] if other else [])
	series = [
		{
			"label": _(stage),
			"color": stage_color.get(stage, NEUTRAL),
			"values": [per_track[c].get(stage, 0) for c in categories],
		}
		for stage in stage_names
	]
	series = [s for s in series if any(s["values"])]  # colours stay fixed per stage
	charts.append(
		{
			"key": "track_stage",
			"kind": "stacked",
			"title": _("Track × Stage"),
			"subtitle": _("Applications in each recruitment track, by current stage."),
			"categories": categories,
			"series": series,
			"total": len(apps),
			"table": {
				"header": [_("Track")] + [s["label"] for s in series] + [_("Total")],
				"rows": [[c] + [s["values"][i] for s in series] + [sum(s["values"][i] for s in series)] for i, c in enumerate(categories)],
				"percent": [],
			},
		}
	)

	# 5. Days in the current status, for applications still moving.
	active = [a for a in apps if a.status not in FINISHED]
	last_change = {}
	if active:
		for row in frappe.get_all(
			"Application Status History",
			filters={"application": ["in", [a.name for a in active]]},
			fields=["application", {"MAX": "changed_on", "as": "changed_on"}],
			group_by="application",
		):
			last_change[row.application] = row.changed_on
	bands = {label: 0 for _lo, _hi, label in AGE_BANDS}
	now = today()
	for a in active:
		since = last_change.get(a.name) or a.application_date or a.creation
		days = max(date_diff(now, getdate(get_datetime(since))), 0)
		for lo, hi, label in AGE_BANDS:
			if days >= lo and (hi is None or days <= hi):
				bands[label] += 1
				break
	charts.append(
		_slice_chart(
			"aging", "column", _("Application Ageing"), _("Days open applications have spent in their current status."),
			[{"label": _(label), "value": bands[label], "color": theme.ramp[i]} for i, (_lo, _hi, label) in enumerate(AGE_BANDS)],
			_("Days in Status"),
		)
	)

	# 6. Source, ranked: too many sources for a pie.
	sources = _count(apps, lambda a: a.source)
	unspecified = sources.pop(None, 0)
	source_slices = [
		{"label": k, "value": v, "color": theme.primary} for k, v in sorted(sources.items(), key=lambda kv: (-kv[1], kv[0]))
	]
	if unspecified:
		source_slices.append({"label": _("Not specified"), "value": unspecified, "color": NEUTRAL})
	charts.append(
		_slice_chart("source", "bar", _("Applications by Source"), _("Where applicants heard about the opening, most first."), source_slices, _("Source"))
	)

	# 7. Category in its own (reservation) order; missing answers in grey.
	categories_count = _count(apps, lambda a: candidates.get(a.candidate, {}).get("category"))
	category_slices = [
		{"label": c, "value": categories_count.pop(c, 0), "color": theme.primary} for c in _select_options("Candidate", "category")
	]
	unknown = categories_count.pop(None, 0)
	category_slices += [{"label": k, "value": v, "color": theme.primary} for k, v in categories_count.items()]
	if unknown:
		category_slices.append({"label": _("Not specified"), "value": unknown, "color": NEUTRAL})
	charts.append(
		_slice_chart("category", "column", _("Applicants by Category"), _("Category declared on each application."), category_slices, _("Category"))
	)

	# 8. Eligibility (status colours, always shown with their labels).
	eligibility = _count(apps, lambda a: a.eligibility_status if a.eligibility_status in ("Eligible", "Not Eligible") else "To check")
	charts.append(
		_slice_chart(
			"eligibility", "donut", _("Eligibility Check"), _("Applications checked against each job's eligibility criteria."),
			[
				{"label": _("Eligible"), "value": eligibility.get("Eligible", 0), "color": STATUS_GOOD},
				{"label": _("Not eligible"), "value": eligibility.get("Not Eligible", 0), "color": STATUS_CRITICAL},
				{"label": _("To check"), "value": eligibility.get("To check", 0), "color": STATUS_WARNING},
			],
			_("Eligibility"),
		)
	)

	# 9. Gender: a small part-to-whole, so a pie.
	charts.append(
		_slice_chart(
			"gender", "pie", _("Applicants by Gender"), _("Gender declared on each application."),
			_slices(
				_count(apps, lambda a: candidates.get(a.candidate, {}).get("gender")),
				theme.palette,
				order=_select_options("Candidate", "gender"),
			),
			_("Gender"),
		)
	)

	# 10. Every job in the selection (zero included), most applications first.
	per_job = _count(apps, lambda a: a.job_opening)
	job_slices = sorted(
		(
			{"label": job.job_title or name, "value": per_job.get(name, 0), "color": theme.primary, "id": name, "track": job.track}
			for name, job in jobs.items()
		),
		key=lambda s: (-s["value"], s["label"].lower()),
	)
	charts.append(
		_slice_chart(
			"job_opening", "bar", _("Applications by Job Opening"), _("Every job opening in this selection, most applications first."),
			job_slices, _("Job Opening"),
		)
	)

	return {"total": len(apps), "charts": charts}


@frappe.whitelist()
def get_report_charts(track=None, job_opening=None, from_date=None, to_date=None):
	"""Every Reports page chart for the filters, plus the filter options."""
	require_pipeline_access()
	data = _charts(_filters(track, job_opening, from_date, to_date), _job_filters(track, job_opening), from_date, to_date)
	data["options"] = {
		"tracks": frappe.get_all("Recruitment Track", pluck="name", order_by="name asc"),
		"jobs": [
			{"value": j.name, "label": j.job_title or j.name, "track": j.track}
			for j in frappe.get_all("Job Opening", fields=["name", "job_title", "track"], order_by="job_title asc")
		],
	}
	return data


@frappe.whitelist()
def export_report(track=None, job_opening=None, from_date=None, to_date=None):
	"""The charts as an Excel workbook: a Summary sheet, then one sheet per
	chart (its table and a native Excel chart), then the pipeline table."""
	require_pipeline_access()
	data = _charts(_filters(track, job_opening, from_date, to_date), _job_filters(track, job_opening), from_date, to_date)
	content = _workbook(data, {"track": track, "job_opening": job_opening, "from_date": from_date, "to_date": to_date})
	frappe.local.response.filename = f"recruitment-report-{today()}.xlsx"
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"


def _excel_chart(chart, ws, first_row, last_row, columns):
	"""A native Excel chart of the same kind over the sheet's table."""
	from openpyxl.chart import BarChart, DoughnutChart, LineChart, PieChart, Reference
	from openpyxl.chart.label import DataLabelList
	from openpyxl.chart.series import DataPoint

	kind = chart["kind"]
	labels = Reference(ws, min_col=1, min_row=first_row + 1, max_row=last_row)
	if kind == "stacked":
		xl = BarChart()
		xl.type, xl.grouping, xl.overlap = "bar", "stacked", 100
		xl.add_data(Reference(ws, min_col=2, max_col=columns - 1, min_row=first_row, max_row=last_row), titles_from_data=True)
		for series, s in zip(xl.series, chart["series"]):
			series.graphicalProperties.solidFill = s["color"][1:]
			series.graphicalProperties.line.solidFill = "FFFFFF"
	else:
		if kind in ("pie", "donut"):
			xl = DoughnutChart(holeSize=55) if kind == "donut" else PieChart()
		elif kind == "line":
			xl = LineChart()
			xl.legend = None
		else:
			xl = BarChart()
			xl.type = "col" if kind == "column" else "bar"
			xl.legend = None
			xl.y_axis.majorGridlines = None
		xl.add_data(Reference(ws, min_col=2, min_row=first_row, max_row=last_row), titles_from_data=True)
		series = xl.series[0]
		if kind == "line":
			series.graphicalProperties.line.solidFill = chart["color"][1:]
			series.graphicalProperties.line.width = 22000  # EMU, about 1.75pt
			series.smooth = False
		else:
			for idx, s in enumerate(chart["slices"]):
				point = DataPoint(idx=idx)
				point.graphicalProperties.solidFill = s["color"][1:]
				point.graphicalProperties.line.solidFill = "FFFFFF"
				series.dPt.append(point)
			series.dLbls = DataLabelList()
			series.dLbls.showVal = True
			series.dLbls.numFmt = "0;;;"  # hide labels of empty groups
	xl.set_categories(labels)
	xl.title = chart["title"]
	rows = last_row - first_row
	if kind in ("bar", "funnel", "stacked"):
		xl.x_axis.scaling.orientation = "maxMin"  # first row at the top, as on the page
		xl.height, xl.width = max(7.5, 0.6 * rows + 3), 22
	elif kind == "line":
		xl.height, xl.width = 8, max(18, min(40, rows * 0.6))
	else:
		xl.height, xl.width = 9, 15
	return xl


def _workbook(data, applied):
	from openpyxl import Workbook
	from openpyxl.styles import Font, PatternFill
	from openpyxl.utils import get_column_letter
	from openpyxl.worksheet.hyperlink import Hyperlink

	from pathways.pathways.report.recruitment_pipeline.recruitment_pipeline import get_columns, get_data
	from pathways.utils.application_export import _sheet_name

	header_font = Font(bold=True, color="FFFFFF")
	header_fill = PatternFill("solid", fgColor=_theme().primary[1:].upper())

	def header(ws, row, values):
		for c, value in enumerate(values, start=1):
			cell = ws.cell(row=row, column=c)
			text(cell, value)
			cell.font, cell.fill = header_font, header_fill

	def text(cell, value):
		# Names come from masters and job titles: never a formula.
		cell.value = value
		cell.data_type = "s"

	wb = Workbook()
	summary = wb.active
	summary.title = _("Summary")
	summary.append([_("Recruitment Report")])
	summary["A1"].font = Font(bold=True, size=14)
	summary.append([_("Exported On"), now_datetime()])
	summary["B2"].number_format = "DD-MMM-YYYY HH:MM"
	summary.append([_("Exported By"), frappe.utils.get_fullname(frappe.session.user)])
	job_title = frappe.db.get_value("Job Opening", applied["job_opening"], "job_title") if applied["job_opening"] else None
	for label, value in (
		(_("Track"), applied["track"] or _("All")),
		(_("Job Opening"), job_title or applied["job_opening"] or _("All")),
		(_("Applied From"), getdate(applied["from_date"]) if applied["from_date"] else _("Any date")),
		(_("Applied To"), getdate(applied["to_date"]) if applied["to_date"] else _("Any date")),
	):
		summary.append([label, None])
		cell = summary.cell(row=summary.max_row, column=2)
		if isinstance(value, datetime.date):
			cell.value, cell.number_format = value, "DD-MMM-YYYY"
		else:
			text(cell, value)
	summary.append([_("Total Applications"), data["total"]])
	summary.append([])
	header(summary, summary.max_row + 1, [_("Sheet"), _("Chart")])

	used = {summary.title.lower()}
	for chart in data["charts"]:
		name = _sheet_name(chart["title"], used)
		ws = wb.create_sheet(name)
		row = summary.max_row + 1
		escaped = name.replace("'", "''")
		link = summary.cell(row=row, column=1)
		text(link, name)
		link.hyperlink = Hyperlink(ref=f"A{row}", location=f"'{escaped}'!A1")
		link.font = Font(color="0563C1", underline="single")
		text(summary.cell(row=row, column=2), chart["subtitle"])

		ws["A1"] = chart["title"]
		ws["A1"].font = Font(bold=True, size=13)
		text(ws["A2"], chart["subtitle"])
		ws["A2"].font = Font(italic=True, color="52514E")
		table = chart["table"]
		header(ws, 4, table["header"])
		for r, values in enumerate(table["rows"], start=5):
			for c, value in enumerate(values, start=1):
				cell = ws.cell(row=r, column=c)
				if isinstance(value, str):
					text(cell, value)
				else:
					cell.value = value
					if c - 1 in table["percent"]:
						cell.number_format = "0.0%"
		last = 4 + len(table["rows"])
		widest = max([len(str(v[0])) for v in table["rows"]] + [len(table["header"][0])])
		ws.column_dimensions["A"].width = max(16, min(60, widest + 2))
		for c in range(2, len(table["header"]) + 1):
			ws.column_dimensions[get_column_letter(c)].width = max(12, len(str(table["header"][c - 1])) + 2)
		ws.freeze_panes = "A5"

		if table["rows"] and chart["total"]:
			anchor = get_column_letter(len(table["header"]) + 2) + "4"
			ws.add_chart(_excel_chart(chart, ws, 4, last, len(table["header"])), anchor)

	# The pipeline table, job titles instead of IDs.
	ws = wb.create_sheet(_sheet_name(_("Pipeline by Job"), used))
	columns = get_columns()
	rows = get_data({k: v for k, v in applied.items() if k in ("track", "job_opening") and v})
	header(ws, 1, [_(c["label"]) for c in columns])
	for r, row in enumerate(rows, start=2):
		for c, col in enumerate(columns, start=1):
			value = row.get(col["fieldname"])
			cell = ws.cell(row=r, column=c)
			if col["fieldtype"] == "Int":
				cell.value = value or 0
			else:
				text(cell, value or "")
	for c, col in enumerate(columns, start=1):
		ws.column_dimensions[get_column_letter(c)].width = 44 if col["fieldname"] == "job_title" else 14
	ws.freeze_panes = "A2"

	summary.column_dimensions["A"].width = 30
	summary.column_dimensions["B"].width = 60
	buffer = io.BytesIO()
	wb.save(buffer)
	return buffer.getvalue()
