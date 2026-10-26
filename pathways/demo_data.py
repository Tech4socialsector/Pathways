# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Realistic demo data: eleven recruitments, each stopped at a different
step of the workflow (one draft, one green sheet returned, one awaiting
approval, one approved, one advertised, one in shortlisting, one with final
interviews coming up, one with interviews done, one green sheet under
approval, one with offers out, one joining next week, one joined).

	bench --site <site> execute pathways.demo_data.create
	bench --site <site> execute pathways.demo_data.delete

Everything is made through the same API calls the screens use, signed in
as the person who would act, with the clock set to the day it would have
happened. Statuses, timelines, approval logs, comments, status history,
email logs, letters and the Employee record therefore come out exactly as
real use would leave them.

People are fictional and use @example.org addresses (a reserved domain).
Every such address is globally unsubscribed, so neither this script nor
anything later (reminders, staff actions on these records) emails them.
All demo users can log in with DEMO_PASSWORD. Development sites only.
"""

import contextlib
import io
import math
import random
import struct
import zipfile
import zlib
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_days, get_datetime, getdate

DOMAIN = "example.org"
DEMO_PASSWORD = "Pathways@Demo2026"
SEED = 2026

# --------------------------------------------------------------- staff
# key: (first, last, title, roles)
STAFF = {
	"kavya": ("Kavya", "Menon", "Executive - People and Culture", ["Pathways Recruiter"]),
	"arjun": ("Arjun", "Nair", "Assistant Manager - People and Culture", ["Pathways Recruiter"]),
	"shalini": ("Shalini", "Hegde", "People and Culture Officer", ["Pathways PNCO"]),
	"meera": ("Meera", "Krishnan", "Director - People and Culture", ["Pathways Director People Culture"]),
	"lakshmi": ("Lakshmi", "Raghavan", "Finance Controller (CFO in charge)", ["Pathways CFO"]),
	"sudha": ("Sudha", "Narayan", "Registrar", ["Pathways Registrar"]),
	"aravind": ("Aravind", "Rao", "Vice Chancellor", ["Pathways Vice Chancellor"]),
	"vikram": ("Vikram", "Desai", "Dean - Academics", ["Pathways Dean Academics"]),
	"anjali": ("Anjali", "Bhatt", "Dean - Research", ["Pathways Dean Research"]),
	"nikhil": ("Nikhil", "Joshi", "Senior Manager - Research", ["Pathways Senior Manager Research"]),
	"divya": ("Divya", "Shetty", "Manager - Communications", ["Pathways Communications"]),
	"manoj": ("Manoj", "Kulkarni", "Executive - IT and Facilities", ["Pathways IT Facilities"]),
	"sanjana": ("Sanjana", "Pillai", "Pathways Administrator", ["Pathways Admin"]),
	# Faculty and external experts: committee roles come from the committees.
	"rahul": ("Rahul", "Sen", "Professor of Law", []),
	"farah": ("Farah", "Siddiqui", "Associate Professor of Law", []),
	"kiran": ("Kiran", "Mathew", "Professor of Sociology", []),
	"pooja": ("Pooja", "Agarwal", "Assistant Professor of Economics", []),
	"thomas": ("Thomas", "Varghese", "Director, Centre for the Study of the Legal Profession", []),
	"sameer": ("Sameer", "Kapoor", "Professor of Law (External Expert)", []),
	"nandini": ("Nandini", "Gupta", "Chartered Accountant (External Expert)", []),
	"rohan": ("Rohan", "Bose", "Professor of Political Science (External Expert)", []),
	"radhika": ("Radhika", "Iyer", "Education Administration Consultant (External Expert)", []),
}
EXTERNAL = {"sameer", "nandini", "rohan", "radhika"}

# ----------------------------------------------------------- candidates
FEMALE = [
	"Aishwarya", "Ananya", "Bhavana", "Chaitra", "Deepa", "Gayathri", "Harini", "Ishita", "Jyothi", "Kritika",
	"Lavanya", "Madhuri", "Nikita", "Pallavi", "Priyanka", "Rashmi", "Sahana", "Shreya", "Sneha", "Swathi",
	"Tanvi", "Usha", "Vaishnavi", "Yamini", "Zoya", "Fathima", "Mercy", "Rukmini", "Sowmya", "Neha",
	"Aparna", "Nithya", "Ritu", "Sanya", "Tara", "Vidya",
]
MALE = [
	"Abhishek", "Aditya", "Akash", "Anand", "Bharath", "Chetan", "Darshan", "Ganesh", "Harish", "Imran",
	"Karthik", "Lokesh", "Mahesh", "Naveen", "Pranav", "Rajat", "Rohit", "Sachin", "Santosh", "Siddharth",
	"Srinivas", "Tejas", "Varun", "Vinay", "Yash", "Joseph", "Faisal", "Gurpreet", "Mohan", "Prakash",
	"Ashwin", "Kunal", "Nitin", "Samuel", "Uday", "Vivek",
]
LAST = [
	"Acharya", "Banerjee", "Bhat", "Chandran", "Das", "D'Souza", "Fernandes", "Ghosh", "Gowda", "Hussain",
	"Iyer", "Jain", "Kamath", "Kaur", "Khan", "Kumar", "Mishra", "Mukherjee", "Murthy", "Naidu",
	"Patil", "Pai", "Prasad", "Qureshi", "Rajan", "Reddy", "Saxena", "Shah", "Sharma", "Shenoy",
	"Singh", "Subramanian", "Thomas", "Upadhyay", "Venkatesh", "Verma", "Wadhwa", "Yadav",
]
LOCALITIES = [
	("Jayanagar 4th Block", "Bengaluru", "560011", "Karnataka"), ("Indiranagar", "Bengaluru", "560038", "Karnataka"),
	("Malleshwaram", "Bengaluru", "560003", "Karnataka"), ("HSR Layout", "Bengaluru", "560102", "Karnataka"),
	("Vijayanagar", "Mysuru", "570017", "Karnataka"), ("Kadri", "Mangaluru", "575002", "Karnataka"),
	("Banjara Hills", "Hyderabad", "500034", "Telangana"), ("Adyar", "Chennai", "600020", "Tamil Nadu"),
	("Kakkanad", "Kochi", "682030", "Kerala"), ("Kothrud", "Pune", "411038", "Maharashtra"),
	("Andheri West", "Mumbai", "400058", "Maharashtra"), ("Salt Lake Sector V", "Kolkata", "700091", "West Bengal"),
	("Saket", "New Delhi", "110017", "Delhi"), ("Gomti Nagar", "Lucknow", "226010", "Uttar Pradesh"),
	("Bodakdev", "Ahmedabad", "380054", "Gujarat"), ("Vaishali Nagar", "Jaipur", "302021", "Rajasthan"),
	("Kankarbagh", "Patna", "800020", "Bihar"), ("Sector 17", "Chandigarh", "160017", "Chandigarh"),
	("Bhubaneswar Old Town", "Bhubaneswar", "751002", "Odisha"), ("Dispur", "Guwahati", "781006", "Assam"),
]

# Education and work by kind of post: (UG, PG, PhD subject, employers, roles)
FAMILIES = {
	"finance": dict(
		ug=["B.Com", "B.Com (Accounting and Finance)", "B.B.A."],
		pg=["M.Com", "MBA (Finance)", "PGDM (Finance)"],
		spec=["Accounting", "Finance", "Taxation", "Corporate Finance"],
		inst=["Christ University, Bengaluru", "St. Joseph's College of Commerce, Bengaluru", "Loyola College, Chennai", "Shri Ram College of Commerce, Delhi", "Symbiosis International University, Pune", "University of Mysore"],
		employers=["Indian Institute of Science, Finance Office", "Manipal Academy of Higher Education", "Azad Educational Trust", "Karnataka State Co-operative Bank", "Grant Thornton Bharat LLP", "Bharat Electronics Limited"],
		roles=["Finance Manager", "Deputy Finance Officer", "Senior Accounts Manager", "Head - Finance and Accounts", "Audit Manager"],
		duties="Statutory and internal audit, budgeting, GST and TDS compliance, fund-flow management and reporting to the governing body.",
	),
	"hr": dict(
		ug=["B.B.A.", "B.A. (Psychology)", "B.Com"],
		pg=["MBA (Human Resources)", "M.A. (Personnel Management)", "MSW (Human Resource Management)", "PGDM (HR)"],
		spec=["Human Resource Management", "Organisational Behaviour", "Industrial Relations"],
		inst=["Christ University, Bengaluru", "Madras School of Social Work", "Tata Institute of Social Sciences, Mumbai", "XLRI Jamshedpur", "Symbiosis Institute of Business Management, Pune", "Bangalore University"],
		employers=["Azim Premji University", "Ashoka Trust for Research in Ecology and the Environment", "Infosys BPM", "Jain (Deemed-to-be University)", "Teach For India", "Dayananda Sagar University"],
		roles=["HR Executive", "Senior Executive - Talent Acquisition", "HR Business Partner", "Assistant Manager - HR"],
		duties="End-to-end recruitment for academic and non-academic roles, onboarding, HRMS records and employee engagement.",
	),
	"pace": dict(
		ug=["B.Sc.", "B.Com", "B.A."],
		pg=["MBA (Operations)", "M.A. (Education)", "MBA", "M.Sc."],
		spec=["Operations Management", "Education Management", "Programme Management"],
		inst=["University of Mysore", "Bangalore University", "Osmania University, Hyderabad", "University of Pune", "Indira Gandhi National Open University", "Jamia Millia Islamia, New Delhi"],
		employers=["Indira Gandhi National Open University, Regional Centre", "Symbiosis Centre for Distance Learning", "upGrad Education", "Christ University, Centre for Online Education", "NIIT Limited"],
		roles=["Assistant Manager - Programme Operations", "Manager - Academic Operations", "Deputy Manager - Distance Education", "Programme Manager"],
		duties="Running admissions-to-certification operations for distance and executive programmes, vendor management and learner support.",
	),
	"design": dict(
		ug=["B.Des. (Communication Design)", "BFA (Applied Art)", "B.Sc. (Visual Communication)"],
		pg=["M.Des. (Graphic Design)", "MFA (Applied Art)", "M.A. (Visual Communication)"],
		spec=["Communication Design", "Graphic Design", "Visual Communication"],
		inst=["Srishti Manipal Institute of Art, Design and Technology", "National Institute of Design, Ahmedabad", "Chitrakala Parishath, Bengaluru", "Sir J.J. School of Art, Mumbai", "MIT Institute of Design, Pune", "Loyola College, Chennai"],
		employers=["Ogilvy India", "Penguin Random House India", "Centre for Policy Research", "Scroll.in", "Freelance Design Studio"],
		roles=["Graphic Designer", "Senior Visual Designer", "Communication Designer", "Design Associate"],
		duties="Print and digital collateral, report layouts, social media creatives and brand guidelines.",
	),
	"law": dict(
		ug=["B.A. LL.B. (Hons.)", "LL.B.", "B.B.A. LL.B. (Hons.)"],
		pg=["LL.M.", "LL.M. (Constitutional Law)", "LL.M. (Business Law)", "LL.M. (Human Rights)"],
		phd="Ph.D. (Law)",
		spec=["Constitutional Law", "Criminal Law", "Corporate Law", "Human Rights Law", "Administrative Law"],
		inst=["National Law School of India University, Bengaluru", "NALSAR University of Law, Hyderabad", "National Law University, Delhi", "West Bengal National University of Juridical Sciences", "Government Law College, Mumbai", "Faculty of Law, University of Delhi"],
		employers=["Vidhi Centre for Legal Policy", "Centre for Law and Policy Research", "High Court of Karnataka (Advocate)", "Jindal Global Law School", "Trilegal", "Daksh India"],
		roles=["Research Fellow", "Associate", "Assistant Professor", "Senior Resident Fellow", "Advocate"],
		teaching_roles=["Assistant Professor of Law", "Associate Professor of Law", "Assistant Professor (Contract)"],
		duties="Teaching undergraduate law courses, supervising dissertations, publishing in peer-reviewed journals and policy research.",
	),
	"ss": dict(
		ug=["B.A. (Economics)", "B.A. (Sociology)", "B.A. (Political Science)", "B.A. (History)"],
		pg=["M.A. (Economics)", "M.A. (Sociology)", "M.A. (Political Science)", "M.Phil. (Sociology)"],
		phd="Ph.D.",
		spec=["Development Economics", "Sociology of Law", "Political Theory", "Public Policy", "Social Anthropology"],
		inst=["Jawaharlal Nehru University, New Delhi", "University of Hyderabad", "Delhi School of Economics", "Tata Institute of Social Sciences, Mumbai", "Presidency University, Kolkata", "Madras Institute of Development Studies"],
		employers=["Azim Premji University", "Institute for Social and Economic Change", "Centre for the Study of Developing Societies", "Christ University", "Ashoka University"],
		roles=["Research Associate", "Assistant Professor", "Post-doctoral Fellow", "Senior Research Fellow"],
		teaching_roles=["Assistant Professor", "Associate Professor", "Guest Faculty"],
		duties="Teaching core social science courses to law students, research methods supervision and field research.",
	),
}

REJECT_REASONS = [
	"Post-graduate degree below the 55% minimum required in the notification.",
	"Does not meet the minimum experience required for the post.",
	"Mandatory qualification (CA / CMA) not held.",
	"Experience is not in a relevant function.",
	"Degree not from a recognised university; transcripts incomplete.",
]


# ===================================================================== entry points


def create():
	"""Create the demo data. Refuses if it already exists."""
	_guard()
	if frappe.db.exists("User", _staff_email("kavya")):
		frappe.throw("Pathways demo data already exists. Run pathways.demo_data.delete first.")
	demo = Demo()
	with _quiet_mail():
		demo.setup_people()
		demo.build_timeline()
		demo.run()
	frappe.db.commit()
	frappe.set_user("Administrator")
	return demo.summary()


def delete():
	"""Remove every demo record (and nothing else)."""
	_guard()
	frappe.set_user("Administrator")
	started = frappe.utils.now_datetime()
	with _inline_jobs(("frappe.model.delete_doc.delete_dynamic_links",)):
		counts = _delete()
	# The empty "Deleted" trail comments this run left on the users, their
	# contacts and settings, and the committee calendar events.
	frappe.db.delete(
		"Comment",
		{
			"comment_type": "Deleted",
			"reference_doctype": ["in", ["User", "Contact", "Notification Settings", "Event", "File"]],
			"reference_name": ["is", "not set"],
			"content": ["is", "not set"],
			"creation": [">=", started],
		},
	)
	frappe.db.commit()
	return counts


def _delete():
	jobs = frappe.get_all("Job Opening", {"owner": ["like", f"%@{DOMAIN}"]}, pluck="name")
	apps = frappe.get_all("Application", {"job_opening": ["in", jobs or [""]]}, pluck="name")
	candidates = list(set(frappe.get_all("Application", {"name": ["in", apps or [""]]}, pluck="candidate")))
	candidates += frappe.get_all("Candidate", {"email": ["like", f"%@{DOMAIN}"], "name": ["not in", candidates or [""]]}, pluck="name")
	by_job = {"job_opening": ["in", jobs or [""]]}
	by_app = {"application": ["in", apps or [""]]}
	interviews = frappe.get_all("Interview", by_app, pluck="name")
	joinings = frappe.get_all("Joining", by_app, pluck="name")
	notifications = frappe.get_all("Recruitment Notification", by_job, pluck="name")
	plan = [
		("Pathways Employee", {"source_application": ["in", apps or [""]]}),
		("IT Facilities Provisioning Request", {"joining": ["in", joinings or [""]]}),
		("Joining", by_app),
		("Document Collection", by_app),
		("Offer Appointment Order", by_app),
		("Post-Interview Green Sheet", by_job),
		("Panel Honorarium", by_job),
		("Reference Check", by_app),
		("Interview Assessment", {"interview": ["in", interviews or [""]]}),
		("Interview", by_app),
		("Selection Committee", by_job),
		("Shortlisting Note", by_job),
		("Shortlisting Score", by_app),
		("Eligibility Check", by_app),
		("Shortlisting Committee", by_job),
		("Application Status History", by_app),
		("Application", {"name": ["in", apps or [""]]}),
		("Application Draft", by_job),
		("Candidate", {"name": ["in", candidates or [""]]}),
		("Corrigendum", by_job),
		("Recruitment Notification", by_job),
		("Pre-Recruitment Green Sheet", by_job),
		("Job Opening", {"name": ["in", jobs or [""]]}),
	]
	counts = {}
	for doctype, filters in plan:
		names = frappe.get_all(doctype, filters, pluck="name")
		for name in names:
			_wipe(doctype, name)
		counts[doctype] = len(names)

	frappe.db.commit()
	_delete_orphans()
	for f in frappe.get_all("File", {"owner": ["like", f"%@{DOMAIN}"], "is_folder": 0}, pluck="name"):
		_wipe("File", f)
	# Job folders (Home/Pathways/<department>/<job>), deepest first; a
	# folder that still holds anything is kept.
	for folder in sorted(frappe.get_all("File", {"owner": ["like", f"%@{DOMAIN}"], "is_folder": 1}, pluck="name"), key=len, reverse=True):
		if not frappe.db.exists("File", {"folder": folder}):
			_wipe("File", folder)

	# Before the users: deleting a user queues jobs that touch this table too.
	frappe.db.delete("Email Unsubscribe", {"email": ["like", f"%@{DOMAIN}"], "global_unsubscribe": 1})
	frappe.db.commit()
	users = frappe.get_all("User", {"name": ["like", f"%@{DOMAIN}"]}, pluck="name")
	for user in users:
		frappe.db.delete("Notification Log", {"for_user": user})
		_wipe("User", user)
	frappe.db.delete("Email Queue", {"sender": ["like", f"%@{DOMAIN}"]})
	# Frappe keeps a deleted user's Contact.
	for contact in frappe.get_all("Contact", {"email_id": ["like", f"%@{DOMAIN}"], "user": ["is", "not set"]}, pluck="name"):
		_wipe("Contact", contact)
	frappe.db.commit()
	counts["User"] = len(users)
	return {k: v for k, v in counts.items() if v}


# ===================================================================== helpers


def _delete_orphans():
	"""Comments, email logs, versions, notifications and calendar events
	left pointing at Pathways records that no longer exist (so a delete
	interrupted half-way is finished by running it again)."""
	pathways = set(frappe.get_all("DocType", {"module": "Pathways"}, pluck="name"))
	for table, dt_field, name_field in (
		("Comment", "reference_doctype", "reference_name"),
		("Communication Log", "reference_doctype", "reference_name"),
		("Version", "ref_doctype", "docname"),
		("Notification Log", "document_type", "document_name"),
		("Event", "reference_doctype", "reference_docname"),
	):
		rows = frappe.get_all(table, {dt_field: ["in", list(pathways)]}, ["name", f"{dt_field} as dt", f"{name_field} as dn"])
		gone = [r.name for r in rows if r.dn and not frappe.db.exists(r.dt, r.dn)]
		for chunk in range(0, len(gone), 500):
			frappe.db.delete(table, {"name": ["in", gone[chunk : chunk + 500]]})
	# Frappe's "Deleted" trail comments, emptied of name and content once
	# the deleted record's links are cleaned up.
	frappe.db.delete(
		"Comment",
		{"comment_type": "Deleted", "reference_doctype": ["in", list(pathways)], "reference_name": ["is", "not set"], "content": ["is", "not set"]},
	)
	frappe.db.commit()



def _guard():
	if not (frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests")):
		frappe.throw("Pathways demo data is for development sites only (set developer_mode or allow_tests).")


def _staff_email(key):
	first, last = STAFF[key][0], STAFF[key][1]
	return f"{first}.{last}@{DOMAIN}".lower()


def _wipe(doctype, name):
	if not frappe.db.exists(doctype, name):
		return
	if frappe.get_meta(doctype).is_submittable:
		frappe.db.set_value(doctype, name, "docstatus", 2, update_modified=False)
	# Pathways' own guards would refuse (records linked to records); other
	# doctypes (User, File, Event) clean up after themselves on trash.
	pathways = frappe.get_meta(doctype).module == "Pathways"
	frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, ignore_on_trash=pathways, delete_permanently=True)


ENQUEUE_OPTIONS = {
	"queue", "timeout", "event", "is_async", "job_name", "now", "enqueue_after_commit", "on_success",
	"on_failure", "at_front", "job_id", "deduplicate",
}


@contextlib.contextmanager
def _inline_jobs(prefixes):
	"""Background jobs whose method starts with one of `prefixes` run in
	place instead of being queued (thousands at once would overload the
	queue); everything else is queued as usual."""
	real_enqueue = frappe.enqueue

	def enqueue(method, *args, **kwargs):
		path = method if isinstance(method, str) else f"{method.__module__}.{method.__qualname__}"
		if not path.startswith(prefixes):
			return real_enqueue(method, *args, **kwargs)
		fn = frappe.get_attr(method) if isinstance(method, str) else method
		return fn(*args, **{k: v for k, v in kwargs.items() if k not in ENQUEUE_OPTIONS})

	frappe.enqueue = enqueue
	try:
		yield
	finally:
		frappe.enqueue = real_enqueue


@contextlib.contextmanager
def _quiet_mail():
	"""Nothing leaves the site while the data is made: sendmail is a no-op,
	and Pathways' background jobs (event emails, portal accounts) run in
	place so their Communication Log and records exist right away."""
	real_sendmail = frappe.sendmail
	frappe.sendmail = lambda *args, **kwargs: None
	try:
		with _inline_jobs(("pathways.",)):
			yield
	finally:
		frappe.sendmail = real_sendmail
		frappe.set_user("Administrator")


@contextlib.contextmanager
def _as(user):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _ascii(text):
	return str(text).encode("ascii", "replace").decode()


def make_pdf(title, lines):
	"""A small one-page PDF with a title and text lines."""

	def esc(text):
		return _ascii(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

	ops = ["BT", "/F2 15 Tf", "56 786 Td", f"({esc(title)}) Tj", "/F1 10 Tf", "0 -28 Td"]
	for line in lines:
		ops += [f"({esc(line)}) Tj", "0 -15 Td"]
	ops.append("ET")
	stream = "\n".join(ops).encode("ascii")
	objects = [
		b"<< /Type /Catalog /Pages 2 0 R >>",
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
		b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
	]
	out = b"%PDF-1.4\n"
	offsets = []
	for i, obj in enumerate(objects, 1):
		offsets.append(len(out))
		out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
	xref = len(out)
	out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
	for offset in offsets:
		out += b"%010d 00000 n \n" % offset
	out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
	return out


def make_png(width, height, pixel):
	"""RGBA PNG from pixel(x, y) -> (r, g, b, a)."""
	raw = b"".join(b"\x00" + bytes(c for x in range(width) for c in pixel(x, y)) for y in range(height))

	def chunk(kind, data):
		return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

	header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
	return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def signature_png(seed):
	"""A handwritten-looking stroke, different for each signer."""
	rng = random.Random(seed)
	a, b, c = rng.uniform(9, 16), rng.uniform(0, 6), rng.uniform(10, 18)

	def curve(x):
		return 40 + c * math.sin(x / a + b) * math.exp(-((x - 120) / 160) ** 2) + 6 * math.sin(x / 5.0 + b)

	def pixel(x, y):
		ink = abs(y - curve(x)) < 1.6 and 14 < x < 226
		return (20, 40, 110, 255) if ink else (255, 255, 255, 0)

	return "data:image/png;base64," + _b64(make_png(240, 80, pixel)).decode()


def photo_png(seed):
	rng = random.Random(seed)
	bg = (rng.randint(150, 210), rng.randint(170, 220), rng.randint(190, 235))
	skin = rng.choice([(224, 172, 105), (198, 134, 66), (141, 85, 36), (241, 194, 125)])

	def pixel(x, y):
		if (x - 60) ** 2 + (y - 55) ** 2 < 28**2:
			return (*skin, 255)
		if y > 95 and (x - 60) ** 2 / 55**2 + (y - 150) ** 2 / 60**2 < 1:
			return (40, 60, 90, 255)
		return (*bg, 255)

	return make_png(120, 150, pixel)


def make_docx(paragraphs):
	body = "".join(
		f"<w:p><w:r><w:t xml:space=\"preserve\">{frappe.utils.escape_html(p)}</w:t></w:r></w:p>" for p in paragraphs
	)
	files = {
		"[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
		"_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
		"word/document.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>',
	}
	buf = io.BytesIO()
	with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
		for path, xml in files.items():
			z.writestr(path, xml)
	return buf.getvalue()


def _b64(data):
	import base64

	return base64.b64encode(data)


def save_file(file_name, content, attach=None):
	"""A private File owned by the session user (as an upload would be)."""
	values = {"doctype": "File", "file_name": file_name, "content": content, "is_private": 1, "folder": "Home"}
	if attach:
		values.update({"attached_to_doctype": attach[0], "attached_to_name": attach[1], "attached_to_field": attach[2] if len(attach) > 2 else None})
	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	return doc


def _slug(text):
	return "".join(ch if ch.isalnum() else "-" for ch in _ascii(text)).strip("-")[:40]


# ===================================================================== the demo


class Demo:
	def __init__(self):
		self.rng = random.Random(SEED)
		self.staff = {}
		self.people = []
		self.used_names = set()
		self.used_mobiles = set()
		self.jobs = {}
		self.events = []

	# ------------------------------------------------------------ people

	def setup_people(self):
		for key, (first, last, title, roles) in STAFF.items():
			email = _staff_email(key)
			self._unsubscribe(email)
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"user_type": "System User",
					"send_welcome_email": 0,
					"bio": title,
					"location": "NLSIU, Bengaluru" if key not in EXTERNAL else None,
					"new_password": DEMO_PASSWORD,
					"roles": [{"role": r} for r in roles],
				}
			)
			user.flags.ignore_password_policy = True
			user.insert(ignore_permissions=True)
			self.staff[key] = email
		frappe.db.commit()

	def _unsubscribe(self, email):
		if not frappe.db.exists("Email Unsubscribe", {"email": email, "global_unsubscribe": 1}):
			frappe.get_doc({"doctype": "Email Unsubscribe", "email": email, "global_unsubscribe": 1}).insert(ignore_permissions=True)

	def _mobile(self):
		while True:
			number = f"{self.rng.choice('6789')}{self.rng.randint(0, 999999999):09d}"
			if number not in self.used_mobiles:
				self.used_mobiles.add(number)
				return number

	def person(self, family, seniority, strength=None):
		"""A fictional applicant. seniority: years of experience (approx)."""
		rng = self.rng
		while True:
			gender = rng.choice(["Female", "Male", "Female", "Male", "Female"])
			first = rng.choice(FEMALE if gender == "Female" else MALE)
			last = rng.choice(LAST)
			if (first, last) not in self.used_names:
				self.used_names.add((first, last))
				break
		email = f"{first}.{last}".lower().replace("'", "") + f"{rng.randint(1, 99)}@{DOMAIN}"
		age = 23 + seniority + rng.randint(0, 3)
		dob = getdate(f"{2026 - age}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}")
		locality, city, pin, state = rng.choice(LOCALITIES)
		person = frappe._dict(
			first=first,
			last=last,
			full_name=f"{first} {last}",
			gender=gender if rng.random() > 0.03 else "Prefer not to say",
			email=email,
			mobile=self._mobile(),
			dob=dob,
			category=rng.choices(["General", "OBC", "SC", "ST"], weights=[55, 27, 12, 6])[0],
			address=f"No. {rng.randint(2, 480)}, {rng.randint(1, 18)}th Cross, {locality}\n{city} - {pin}, {state}",
			family=family,
			seniority=seniority,
			strength=strength if strength is not None else rng.random(),
			seq=len(self.people),
		)
		self.people.append(person)
		self._unsubscribe(email)
		return person

	# ------------------------------------------------------------ scheduling

	def at(self, when, fn, *args):
		self.events.append((get_datetime(when), len(self.events), fn, args))

	def run(self):
		from frappe.tests.classes.context_managers import freeze_time

		for when, _seq, fn, args in sorted(self.events, key=lambda e: (e[0], e[1])):
			with freeze_time(when, tick=True):
				fn(*args)
				frappe.db.commit()

	def summary(self):
		return {
			"jobs": len(self.jobs),
			"applications": frappe.db.count("Application", {"job_opening": ["in", [j.name for j in self.jobs.values() if j.name] or [""]]}),
			"candidates": len(self.people),
			"staff": len(self.staff),
			"password": DEMO_PASSWORD,
		}

	# ===================================================================== timeline

	def build_timeline(self):
		D = datetime.fromisoformat
		# 1. Chief Finance Officer: the full cycle, joined on 1 Oct.
		self.job(
			"cfo", "ADM-CFO", "Chief Finance Officer", "finance", vacancies=1, raiser="arjun",
			created=D("2026-06-01 10:05"), gs=D("2026-06-01 11:30"),
			approvals=[D("2026-06-02 12:10"), D("2026-06-04 16:40"), D("2026-06-08 11:15"), D("2026-06-10 18:05")],
			notice=(D("2026-06-11 15:00"), "6/2026"), advertise=(D("2026-06-12 10:00"), D("2026-07-03 17:00")),
			applicants=[(18, 0.9), (16, 0.82), (20, 0.75), (15, 0.6), (17, 0.55), (14, 0.5), (19, 0.45), (12, 0.4), (16, 0.35), (13, 0.3), (8, 0.15), (10, 0.12), (6, 0.08), (11, 0.25)],
			committee=(D("2026-07-06 11:00"), ["meera", "lakshmi"], "NLSIU/PNC/OO/2026/041"),
			eligibility=D("2026-07-08 15:20"), scoring=(D("2026-07-10 12:00"), 5, 1.0), regrets=D("2026-07-14 11:00"),
			hr=(D("2026-07-15 10:30"), D("2026-07-20 10:00"), ["kavya", "arjun"], D("2026-07-20 15:30")),
			final_shortlist=D("2026-07-22 12:00"),
			panel=(D("2026-07-23 11:00"), ["aravind", "sudha", "meera", "nandini"], D("2026-08-04 10:30")),
			final=(D("2026-07-24 10:00"), "In-Person", 45, D("2026-08-04 16:30"), 1.0),
			outcomes=(D("2026-08-05 11:00"), True),
			references=(D("2026-08-06 10:00"), D("2026-08-08 16:00"), "all"),
			post_regrets=D("2026-08-10 11:30"), thanks=(D("2026-08-10 12:00"), 15000, D("2026-08-14 15:00"), D("2026-08-20 11:00")),
			post_gs=(D("2026-08-11 10:30"), [D("2026-08-12 11:00"), D("2026-08-13 15:30"), D("2026-08-17 12:20"), D("2026-08-19 17:45"), D("2026-08-21 10:15")]),
			offers=[dict(create=D("2026-08-24 10:00"), review=D("2026-08-24 16:00"), approve=D("2026-08-25 11:30"), sign=D("2026-08-26 10:45"), send=D("2026-08-26 15:00"), respond=(D("2026-08-29 20:10"), "Accepted", "2026-10-01"))],
			onboarding=dict(upload=(D("2026-09-03 19:00"), D("2026-09-12 21:00")), verify=D("2026-09-15 12:00"), confirm=D("2026-09-16 11:00"), it=(D("2026-09-24 16:00"), D("2026-09-29 17:30")), joined=D("2026-10-01 10:30")),
			filled=D("2026-10-01 12:00"), waitlist_regret=D("2026-10-05 11:00"),
		)
		# 2. Assistant Manager - People and Culture: joins on 2 Nov; documents and IT under way.
		self.job(
			"pnc", "ADM-AM-PNC", "Assistant Manager - People and Culture", "hr", vacancies=1, raiser="kavya",
			created=D("2026-07-20 10:00"), gs=D("2026-07-20 12:00"),
			approvals=[D("2026-07-21 10:30"), D("2026-07-23 15:10"), D("2026-07-27 11:40"), D("2026-07-30 17:20")],
			notice=(D("2026-07-31 16:00"), "11/2026"), advertise=(D("2026-08-03 10:00"), D("2026-08-24 17:00")),
			applicants=[(6, 0.92), (5, 0.8), (7, 0.7), (4, 0.62), (5, 0.58), (3, 0.5), (6, 0.47), (4, 0.4), (2, 0.2), (8, 0.36), (3, 0.3), (1, 0.1), (5, 0.33), (4, 0.28), (2, 0.18), (6, 0.42)],
			committee=(D("2026-08-26 11:00"), ["meera", "shalini"], "NLSIU/PNC/OO/2026/058"),
			eligibility=D("2026-08-27 16:00"), scoring=(D("2026-08-29 12:30"), 5, 1.0), regrets=D("2026-09-01 11:00"),
			hr=(D("2026-09-01 15:00"), D("2026-09-03 10:00"), ["kavya", "arjun"], D("2026-09-03 16:00")),
			final_shortlist=D("2026-09-04 12:00"),
			panel=(D("2026-09-04 15:00"), ["sudha", "meera", "shalini", "radhika"], D("2026-09-16 11:00")),
			final=(D("2026-09-05 10:00"), "In-Person", 40, D("2026-09-16 17:00"), 1.0),
			outcomes=(D("2026-09-17 10:30"), True),
			references=(D("2026-09-18 10:00"), D("2026-09-22 15:00"), "all"),
			post_regrets=D("2026-09-21 11:30"), thanks=(D("2026-09-21 12:00"), 10000, D("2026-09-28 15:00"), None),
			post_gs=(D("2026-09-23 10:30"), [D("2026-09-24 11:00"), D("2026-09-25 15:30"), D("2026-09-29 12:20"), D("2026-10-01 17:45"), D("2026-10-05 10:15")]),
			offers=[dict(create=D("2026-10-06 10:00"), review=D("2026-10-06 15:00"), approve=D("2026-10-07 11:30"), sign=D("2026-10-08 12:00"), send=D("2026-10-09 10:30"), respond=(D("2026-10-13 18:40"), "Accepted", "2026-11-02"))],
			onboarding=dict(upload=(D("2026-10-15 19:00"), D("2026-10-22 21:00")), partial=True, verify=D("2026-10-23 12:00"), confirm=D("2026-10-20 11:00"), it=(D("2026-10-24 12:00"), None)),
		)
		# 3. Associate Professor (Law), 2 posts: one offer sent, one awaiting the Registrar.
		self.job(
			"assoc_law", "FAC-ASSOC-LAW", "Associate Professor (Law)", "law", vacancies=2, raiser="kavya",
			reservation=[("General", 1), ("SC", 1)],
			created=D("2026-06-15 10:00"), gs=D("2026-06-15 12:30"),
			approvals=[D("2026-06-16 11:00"), D("2026-06-18 15:00"), D("2026-06-22 12:00"), D("2026-06-25 16:30"), D("2026-06-29 11:00")],
			notice=(D("2026-06-30 15:00"), "7/2026"), advertise=(D("2026-07-01 10:00"), D("2026-07-31 17:00")),
			corrigendum=(D("2026-07-29 12:00"), D("2026-08-10 17:00"), "Closing date extended at the request of several applicants awaiting API score verification."),
			applicants=[(14, 0.95), (12, 0.88), (11, 0.8), (13, 0.72), (10, 0.66), (12, 0.55), (9, 0.5), (10, 0.42), (8, 0.35), (15, 0.6), (6, 0.12), (7, 0.2)],
			committee=(D("2026-08-12 11:00"), ["rahul", "farah", "vikram"], "NLSIU/ACAD/OO/2026/112"),
			eligibility=D("2026-08-14 15:00"), scoring=(D("2026-08-18 12:00"), 5, 1.0), regrets=D("2026-08-25 11:00"),
			panel=(D("2026-08-27 11:00"), ["aravind", "vikram", "sudha", "rahul", "sameer"], D("2026-09-15 10:00")),
			final=(D("2026-08-28 10:00"), "In-Person", 60, D("2026-09-15 18:00"), 1.0),
			outcomes=(D("2026-09-17 11:00"), True),
			references=(D("2026-09-18 10:00"), D("2026-09-25 15:00"), "all"),
			post_regrets=D("2026-09-21 11:30"), thanks=(D("2026-09-21 12:30"), 20000, D("2026-09-28 15:00"), D("2026-10-06 11:00")),
			post_gs=(D("2026-09-24 10:30"), [D("2026-09-25 11:00"), D("2026-09-28 15:30"), D("2026-09-30 12:20"), D("2026-10-05 17:45"), D("2026-10-07 10:15")]),
			post_gs_second=(D("2026-10-08 10:30"), [D("2026-10-09 11:00"), D("2026-10-12 15:30"), D("2026-10-14 12:20"), D("2026-10-16 17:45"), D("2026-10-19 10:15")]),
			offers=[
				dict(create=D("2026-10-12 10:00"), review=D("2026-10-13 11:00"), returned=(D("2026-10-14 12:00"), "Probation should read two years, as in Notification No. 7/2026.", D("2026-10-15 10:30")), approve=D("2026-10-16 11:30"), sign=D("2026-10-21 12:00"), send=D("2026-10-22 10:30")),
				dict(create=D("2026-10-20 10:00"), review=D("2026-10-21 11:00"), approve=D("2026-10-23 15:30")),
			],
		)
		# 4. Research Associate (WILL), 2 posts: selection green sheet with the Dean (Research).
		self.job(
			"ra_will", "RES-RA-WILL", "Research Associate - Women's Inclusion and Leadership in Law (WILL) Initiative", "law", vacancies=2, raiser="arjun",
			created=D("2026-08-10 10:00"), gs=D("2026-08-10 12:00"),
			approvals=[D("2026-08-11 11:00"), D("2026-08-13 15:00"), D("2026-08-17 12:00"), D("2026-08-19 16:30"), D("2026-08-21 11:00")],
			notice=(D("2026-08-21 17:00"), "12/2026"), advertise=(D("2026-08-24 10:00"), D("2026-09-14 17:00")),
			applicants=[(3, 0.9), (2, 0.85), (4, 0.78), (2, 0.7), (3, 0.65), (5, 0.6), (2, 0.4), (1, 0.15), (3, 0.5), (2, 0.35), (4, 0.3), (1, 0.1), (2, 0.25), (3, 0.45), (2, 0.55)],
			committee=(D("2026-09-16 11:00"), ["nikhil", "thomas"], "NLSIU/RES/OO/2026/019"),
			eligibility=D("2026-09-17 15:00"), scoring=(D("2026-09-19 12:00"), 6, 1.0), regrets=D("2026-09-23 11:00"),
			panel=(D("2026-09-24 11:00"), ["anjali", "thomas", "nikhil", "rohan"], D("2026-10-08 10:00")),
			final=(D("2026-09-25 10:00"), "Video Conference", 30, D("2026-10-08 16:00"), 1.0),
			outcomes=(D("2026-10-09 11:00"), True),
			references=(D("2026-10-12 10:00"), D("2026-10-14 15:00"), "first"),
			post_regrets=D("2026-10-12 11:30"), thanks=(D("2026-10-12 12:30"), 7500, None, None),
			post_gs=(D("2026-10-16 10:30"), [D("2026-10-19 11:00"), D("2026-10-20 15:30"), D("2026-10-22 12:20")]),
		)
		# 5. Assistant Professor (Social Science), 2-year contract: final interviews held on 23 Oct.
		self.job(
			"ap_ss", "FAC-AP-SS-2Y", "Assistant Professor (Social Science) - 2-Year Contract", "ss", vacancies=3, raiser="kavya",
			created=D("2026-08-03 10:00"), gs=D("2026-08-03 12:00"),
			approvals=[D("2026-08-04 11:00"), D("2026-08-06 15:00"), D("2026-08-10 12:00"), D("2026-08-12 16:30"), D("2026-08-13 11:00")],
			notice=(D("2026-08-14 15:00"), "13/2026"), advertise=(D("2026-08-17 10:00"), D("2026-09-11 17:00")),
			applicants=[(5, 0.9), (4, 0.84), (6, 0.8), (3, 0.74), (4, 0.7), (5, 0.66), (3, 0.6), (2, 0.5), (4, 0.4), (2, 0.3), (1, 0.12), (3, 0.35), (2, 0.2), (5, 0.55)],
			committee=(D("2026-09-15 11:00"), ["kiran", "pooja"], "NLSIU/ACAD/OO/2026/131"),
			eligibility=D("2026-09-18 15:00"), scoring=(D("2026-09-22 12:00"), 7, 1.0), regrets=D("2026-09-28 11:00"),
			panel=(D("2026-10-05 11:00"), ["aravind", "vikram", "kiran", "pooja", "rohan"], D("2026-10-23 10:00")),
			final=(D("2026-10-06 10:00"), "Video Conference", 40, D("2026-10-23 18:00"), 0.75),
			rsvp_decline=True, tag=(D("2026-09-20 10:00"), "rahul", "Comparative view on the social science shortlist."),
		)
		# 6. Manager - PACE: HR round done; final interviews on 29 Oct.
		self.job(
			"pace", "ADM-MGR-PACE", "Manager - Professional and Continuing Education (PACE)", "pace", vacancies=1, raiser="arjun",
			created=D("2026-07-13 10:00"), gs=D("2026-07-14 11:00"),
			approvals=[D("2026-07-15 11:00"), D("2026-07-17 15:00"), D("2026-07-22 12:00"), D("2026-07-27 16:30")],
			notice=(D("2026-07-30 12:00"), "10/2026"), advertise=(D("2026-07-30 15:00"), D("2026-08-20 17:00")),
			corrigendum=(D("2026-08-20 10:00"), D("2026-09-03 17:00"), "Last date for receipt of applications extended to 03.09.2026, 5 pm."),
			applicants=[(9, 0.9), (8, 0.8), (10, 0.75), (7, 0.66), (11, 0.6), (6, 0.5), (8, 0.45), (4, 0.2), (9, 0.4), (5, 0.3), (7, 0.35), (3, 0.1), (8, 0.55)],
			committee=(D("2026-09-08 11:00"), ["meera", "kavya"], "NLSIU/PNC/OO/2026/066"),
			eligibility=D("2026-09-10 15:00"), scoring=(D("2026-09-15 12:00"), 5, 1.0), regrets=D("2026-09-18 11:00"),
			hr=(D("2026-09-22 10:30"), D("2026-09-29 10:00"), ["kavya", "arjun"], D("2026-09-29 15:30")),
			final_shortlist=D("2026-10-01 12:00"),
			panel=(D("2026-10-12 11:00"), ["aravind", "sudha", "meera", "radhika"], D("2026-10-29 11:00")),
			final=(D("2026-10-13 10:00"), "In-Person", 45, None, 0),
			rsvp_partial=True,
		)
		# 7. Assistant Professor (Law), 2-year contract: shortlisting in progress.
		self.job(
			"ap_law", "FAC-AP-LAW-2Y", "Assistant Professor (Law) - 2-Year Contract", "law", vacancies=4, raiser="kavya",
			created=D("2026-08-24 10:00"), gs=D("2026-08-24 12:00"),
			approvals=[D("2026-08-25 11:00"), D("2026-08-27 15:00"), D("2026-08-31 12:00"), D("2026-09-02 16:30"), D("2026-09-03 11:00")],
			notice=(D("2026-09-04 15:00"), "14/2026"), advertise=(D("2026-09-05 10:00"), D("2026-10-05 17:00")),
			applicants=[(4, 0.9), (3, 0.85), (5, 0.8), (2, 0.75), (3, 0.7), (4, 0.65), (2, 0.6), (3, 0.55), (1, 0.5), (2, 0.45), (3, 0.4), (1, 0.3), (2, 0.25), (1, 0.15), (4, 0.62), (2, 0.35), (3, 0.52), (1, 0.08)],
			committee=(D("2026-10-08 11:00"), ["rahul", "farah"], "NLSIU/ACAD/OO/2026/147"),
			eligibility=(D("2026-10-12 15:00"), 15), scoring=(D("2026-10-19 12:00"), 4, 0.5),
		)
		# 8. Graphic Designer: advertised, applications coming in.
		self.job(
			"gd", "ADM-GD", "Graphic Designer", "design", vacancies=1, raiser="arjun",
			created=D("2026-10-05 10:00"), gs=D("2026-10-05 12:00"),
			approvals=[D("2026-10-06 11:00"), D("2026-10-07 15:00"), D("2026-10-12 12:00"), D("2026-10-14 16:30")],
			notice=(D("2026-10-15 11:00"), "16/2026"), advertise=(D("2026-10-15 15:00"), D("2026-11-08 17:00")),
			applicants=[(4, 0.8), (2, 0.6), (6, 0.85), (3, 0.5), (1, 0.3), (5, 0.7), (2, 0.4), (3, 0.65), (4, 0.55)],
			withdraw=D("2026-10-24 19:30"), tag=(D("2026-10-16 10:00"), "pooja", "Help assess portfolios for academic publication design."),
		)
		# 9. Project Director (WILL): green sheet with the Dean (Research).
		self.job(
			"pd_will", "RES-PD-WILL", "Project Director - Women's Inclusion and Leadership in Law (WILL) Initiative", "law", vacancies=1, raiser="arjun",
			created=D("2026-10-14 10:00"), gs=D("2026-10-15 11:00"),
			approvals=[D("2026-10-16 12:00"), D("2026-10-20 15:30")],
		)
		# 10. Associate Professor (HSS): green sheet returned for revision.
		self.job(
			"assoc_hss", "FAC-ASSOC-HSS", "Associate Professor (Humanities and Social Science)", "ss", vacancies=2, raiser="kavya",
			created=D("2026-10-16 10:00"), gs=D("2026-10-19 11:00"),
			approvals=[D("2026-10-20 12:00")],
			returned=(D("2026-10-22 16:00"), "Please attach the Academic Council resolution approving the two posts and confirm the reservation roster point for the second vacancy."),
		)
		# 11. Assistant Manager - Finance: approved, notification being drafted.
		self.job(
			"am_fin", "ADM-AM-FIN", "Assistant Manager - Finance", "finance", vacancies=1, raiser="kavya",
			created=D("2026-09-28 10:00"), gs=D("2026-09-29 11:00"),
			approvals=[D("2026-09-30 11:00"), D("2026-10-05 15:00"), D("2026-10-09 12:00"), D("2026-10-13 16:30")],
			draft_notice=(D("2026-10-16 15:00"), "17/2026"),
		)

	# ------------------------------------------------------------ one job

	def job(self, key, position, title, family, vacancies, raiser, created, gs, approvals, **spec):
		job = frappe._dict(key=key, position=position, title=title, family=family, vacancies=vacancies, raiser=raiser, spec=spec, name=None, apps=[])
		self.jobs[key] = job
		self.at(created, self.create_job, job)
		self.at(gs, self.raise_green_sheet, job)
		for i, when in enumerate(approvals):
			self.at(when, self.approve_green_sheet, job, i)
		if spec.get("returned"):
			when, remarks = spec["returned"]
			self.at(when, self.return_green_sheet, job, remarks)
		if spec.get("draft_notice"):
			self.at(spec["draft_notice"][0], self.save_notice, job, spec["draft_notice"][1])
		if not spec.get("notice"):
			return
		self.at(spec["notice"][0], self.save_notice, job, spec["notice"][1])
		start, deadline = spec["advertise"]
		self.at(start, self.advertise, job, start, deadline)
		self.at(start + timedelta(hours=3), self.publish, job)
		if spec.get("tag"):
			self.at(spec["tag"][0], self.tag_colleague, job, spec["tag"][1], spec["tag"][2])

		closing = deadline
		if spec.get("corrigendum"):
			when, new_deadline, remarks = spec["corrigendum"]
			self.at(when, self.corrigendum, job, new_deadline, remarks)
			closing = new_deadline
		# Applications spread over the window (the newest ones close to today
		# for a job still open).
		last = min(closing, datetime(2026, 10, 26, 9, 0)) - timedelta(hours=2)
		window = (last - start).total_seconds()
		for i, (years, strength) in enumerate(spec["applicants"]):
			who = self.person(family, years, strength)
			offset = window * (i + self.rng.random() * 0.8) / len(spec["applicants"])
			when = start + timedelta(seconds=offset + 3600)
			when = min(max(when.replace(hour=max(8, min(when.hour, 22))), start + timedelta(minutes=30)), last)
			self.at(when, self.apply, job, who)
		if closing < datetime(2026, 10, 26):
			self.at(closing + timedelta(hours=1), self.close_ads)
		if spec.get("withdraw"):
			self.at(spec["withdraw"], self.withdraw, job)

		if spec.get("committee"):
			self.at(spec["committee"][0], self.shortlisting_committee, job)
		if spec.get("eligibility"):
			value = spec["eligibility"]
			when, limit = value if isinstance(value, tuple) else (value, None)
			self.at(when, self.eligibility, job, limit)
		if spec.get("scoring"):
			self.at(spec["scoring"][0], self.score, job)
		if spec.get("regrets"):
			self.at(spec["regrets"], self.shortlisting_regrets, job)
		if spec.get("hr"):
			scheduled_on, interview_at, _assessors, assessed = spec["hr"]
			self.at(scheduled_on, self.schedule_hr, job)
			self.at(scheduled_on + timedelta(hours=20), self.rsvp, job, "HR Interaction", False)
			self.at(assessed, self.assess_hr, job)
		if spec.get("final_shortlist"):
			self.at(spec["final_shortlist"], self.final_shortlist, job)
		if spec.get("panel"):
			self.at(spec["panel"][0], self.selection_committee, job)
		if spec.get("final"):
			scheduled_on, _mode, _slot, assessed, _share = spec["final"]
			self.at(scheduled_on, self.schedule_final, job)
			self.at(scheduled_on + timedelta(hours=26), self.rsvp, job, "Final", spec.get("rsvp_partial"))
			if assessed:
				self.at(assessed, self.assess_final, job)
		if spec.get("outcomes"):
			self.at(spec["outcomes"][0], self.record_outcomes, job)
		if spec.get("references"):
			self.at(spec["references"][0], self.request_references, job)
			self.at(spec["references"][1], self.record_references, job)
		if spec.get("post_regrets"):
			self.at(spec["post_regrets"], self.post_interview_regrets, job, 0)
		if spec.get("thanks"):
			when, amount, approved, paid = spec["thanks"]
			self.at(when, self.panel_thanks, job, amount)
			if approved:
				self.at(approved, self.approve_honoraria, job)
			if paid:
				self.at(paid, self.pay_honoraria, job)
		if spec.get("post_gs"):
			self.at(spec["post_gs"][0], self.raise_post_gs, job, 0)
			for i, when in enumerate(spec["post_gs"][1]):
				self.at(when, self.approve_post_gs, job, 0, i)
		if spec.get("post_gs_second"):
			self.at(spec["post_gs_second"][0], self.raise_post_gs, job, 1)
			for i, when in enumerate(spec["post_gs_second"][1]):
				self.at(when, self.approve_post_gs, job, 1, i)
		for i, offer in enumerate(spec.get("offers") or []):
			self.at(offer["create"], self.offer_create, job, i)
			self.at(offer["review"], self.offer_review, job, i)
			if offer.get("returned"):
				when, remarks, again = offer["returned"]
				self.at(when, self.offer_return, job, i, remarks)
				self.at(again, self.offer_review, job, i)
			self.at(offer["approve"], self.offer_approve, job, i)
			if offer.get("sign"):
				self.at(offer["sign"], self.offer_sign, job, i)
			if offer.get("send"):
				self.at(offer["send"], self.offer_send, job, i)
			if offer.get("respond"):
				self.at(offer["respond"][0], self.offer_respond, job, i)
		onboarding = spec.get("onboarding")
		if onboarding:
			start, end = onboarding["upload"]
			self.at(start, self.upload_documents, job, start, end)
			self.at(onboarding["verify"], self.verify_documents, job)
			self.at(onboarding["confirm"], self.confirm_joining, job)
			self.at(onboarding["it"][0], self.it_progress, job)
			if onboarding["it"][1]:
				self.at(onboarding["it"][1], self.it_complete, job)
			if onboarding.get("joined"):
				self.at(onboarding["joined"], self.mark_joined, job)
		if spec.get("filled"):
			self.at(spec["filled"], self.fill_job, job)
		if spec.get("waitlist_regret"):
			self.at(spec["waitlist_regret"], self.post_interview_regrets, job, 1)

	# ===================================================================== steps

	def s(self, key):
		return self.staff[key]

	# ------------------------------------------------------------ job and green sheet

	def create_job(self, job):
		from pathways.api.job_opening import create_job_opening

		position = frappe.get_doc("Position", job.position)
		data = {
			"position": job.position,
			"job_title": job.title,
			"track": position.track,
			"department": position.department,
			"designation": position.designation,
			"employment_type": position.employment_type,
			"vacancies": job.vacancies,
			"pay_level": position.pay_level or PAY.get(job.position),
			"tenure_description": position.tenure_description or TENURE.get(position.employment_type),
			"jd_text": jd_html(job, position),
			"shortlisting_ratio": 5,
		}
		if job.spec.get("reservation"):
			data["reservation_breakdown"] = [{"category": c, "vacancy_count": n} for c, n in job.spec["reservation"]]
		with _as(self.s(job.raiser)):
			doc = create_job_opening(data)
		job.name = doc["name"]
		job.track = position.track
		jd = make_pdf(f"Job Description - {job.title}", jd_lines(job, position))
		with _as(self.s(job.raiser)):
			file = save_file(f"JD-{_slug(job.title)}.pdf", jd, ("Job Opening", job.name, "jd_attachment"))
		frappe.db.set_value("Job Opening", job.name, "jd_attachment", file.file_url, update_modified=False)
		job.jd = file.file_url

	def raise_green_sheet(self, job):
		from pathways.api.green_sheet import save_green_sheet

		with _as(self.s(job.raiser)):
			job.green_sheet = save_green_sheet(
				job.name,
				justification_html(job),
				duration_of_ad_days=21 if job.track != "Faculty" else 30,
				submit=1,
				jd_attachment=job.jd,
			)

	def _approve(self, doctype, name, remarks_pool, action="Approved", remarks=None):
		from pathways.api.approval import record_approval_action
		from pathways.utils.approval import get_current_step, get_step_users

		doc = frappe.get_doc(doctype, name)
		step = get_current_step(doc)
		users = [u for u in get_step_users(step) if u.endswith(f"@{DOMAIN}")]
		done = {row.approver for row in doc.approval_log}
		user = next((u for u in users if u not in done), None)
		if not user:
			frappe.throw(f"No demo approver for {doctype} {name} step {step.sequence} ({step.approver_role}).")
		channel = "Signature" if step.approver_role in ("Pathways Vice Chancellor", "Pathways Registrar") and self.rng.random() < 0.5 else "Digital"
		with _as(user):
			record_approval_action(doctype, name, action, remarks or self.rng.choice(remarks_pool), channel)

	def approve_green_sheet(self, job, _i):
		self._approve("Pre-Recruitment Green Sheet", job.green_sheet, APPROVAL_REMARKS)

	def return_green_sheet(self, job, remarks):
		self._approve("Pre-Recruitment Green Sheet", job.green_sheet, [], action="Returned for Revision", remarks=remarks)

	# ------------------------------------------------------------ notification and advert

	def save_notice(self, job, number):
		from pathways.api.job_notice import save_job_notice

		publish = frappe.utils.today()
		with _as(self.s(job.raiser)):
			pdf = make_pdf(
				f"NATIONAL LAW SCHOOL OF INDIA UNIVERSITY - Notification No. {number}",
				[
					f"Dated: {frappe.utils.formatdate(publish, 'dd.MM.yyyy')}",
					"",
					f"Applications are invited for the post of {job.title}.",
					f"Number of vacancies: {job.vacancies}",
					"Eligibility, pay and the application process are given in the detailed advertisement",
					"published on the University website.",
					"",
					"Sd/-",
					"Registrar",
				],
			)
			file = save_file(f"Notification-No-{number.replace('/', '-')}-{_slug(job.title)}.pdf", pdf, ("Job Opening", job.name))
			save_job_notice(
				job.name,
				{
					"notification_number": f"Notification No. {number}",
					"publish_date": publish,
					"notification_url": f"https://www.nls.ac.in/wp-content/uploads/2026/notification-no-{number.replace('/', '-')}.pdf",
					"notification_attachment": file.file_url,
				},
			)

	def advertise(self, job, start, deadline):
		from pathways.api.job_opening import update_job_opening

		with _as(self.s(job.raiser)):
			update_job_opening(job.name, {"status": "Advertised", "application_start": str(start), "application_deadline": str(deadline)})

	def publish(self, job):
		from pathways.api.job_notice import save_publishing

		slug = _slug(job.title).lower()
		today = frappe.utils.today()
		data = {
			"website_url": f"https://www.nls.ac.in/recruitment/{slug}/",
			"website_published_on": today,
			"linkedin_url": f"https://www.linkedin.com/feed/update/urn:li:activity:{7300000000000000000 + self.rng.randint(1, 10**15)}/",
			"linkedin_published_on": today,
		}
		if job.track == "Admin":
			data.update({"indeed_url": f"https://in.indeed.com/viewjob?jk={frappe.generate_hash(length=16)}", "indeed_published_on": today})
		with _as(self.s("divya")):
			save_publishing(job.name, data)

	def tag_colleague(self, job, key, note):
		from pathways.api.job_opening import set_job_colleagues

		with _as(self.s(job.raiser)):
			set_job_colleagues(job.name, [{"user": self.s(key), "access_note": note}])

	def corrigendum(self, job, new_deadline, remarks):
		from pathways.api.job_notice import issue_corrigendum

		with _as(self.s("sudha")):
			pdf = make_pdf("CORRIGENDUM", [f"Post: {job.title}", remarks, f"Revised last date: {frappe.utils.format_datetime(new_deadline, 'dd.MM.yyyy, h:mm a')}", "", "Sd/-", "Registrar"])
			file = save_file(f"Corrigendum-{_slug(job.title)}.pdf", pdf)
			issue_corrigendum(job.name, "Closing Date", new_value=str(new_deadline), remarks=remarks, corrigendum_attachment=file.file_url)

	def close_ads(self):
		from pathways.tasks import close_expired_job_openings

		close_expired_job_openings()

	# ------------------------------------------------------------ applications

	def apply(self, job, who):
		from pathways.api.application import submit_application
		from pathways.utils.candidate_account import create_portal_account

		has_login = frappe.db.exists("User", who.email)
		user = who.email if has_login else "Guest"
		job_doc = frappe.get_doc("Job Opening", job.name)
		with _as(user):
			data = ApplicationForm(self, job, job_doc, who, user).build()
			result = submit_application(job.name, data)
		app = result["application_name"]
		if not has_login:
			# The portal login the first application creates (a background job in real use).
			create_portal_account(result["candidate_id"])
			from frappe.utils.password import update_password

			update_password(who.email, DEMO_PASSWORD)
			frappe.db.set_value("Candidate", result["candidate_id"], "password_change_required", 0, update_modified=False)
		job.apps.append(frappe._dict(name=app, who=who))

	def withdraw(self, job):
		from pathways.api.application import withdraw_application

		app = min(job.apps, key=lambda a: a.who.strength)
		with _as(app.who.email):
			withdraw_application(app.name)
		app.withdrawn = True

	def _live(self, job):
		return [a for a in job.apps if not a.get("withdrawn")]

	# ------------------------------------------------------------ shortlisting

	def shortlisting_committee(self, job):
		from pathways.api.scoring import create_shortlisting_committee

		when, members, order = job.spec["committee"]
		with _as(self.s(job.raiser)):
			pdf = make_pdf("OFFICE ORDER", [f"No. {order}", f"Constitution of the Shortlisting Committee for the post of {job.title}.", "Members:", *[f"  - {frappe.utils.get_fullname(self.s(m))}, {STAFF[m][2]}" for m in members], "", "Sd/- Registrar"])
			file = save_file(f"Office-Order-{order.replace('/', '-')}.pdf", pdf)
			job.committee = create_shortlisting_committee(
				job.name, [self.s(m) for m in members], order, shortlisting_deadline=add_days(getdate(when), 7), office_order_attachment=file.file_url
			)
		job.committee_members = members

	def eligibility(self, job, limit=None):
		from pathways.api.scoring import set_eligibility

		apps = sorted(self._live(job), key=lambda a: a.name)
		if limit:
			apps = apps[:limit]
		for i, app in enumerate(apps):
			member = self.s(job.committee_members[i % len(job.committee_members)])
			eligible = app.who.strength >= 0.2
			reason = None if eligible else self.rng.choice(REJECT_REASONS[:2] + ([REJECT_REASONS[2]] if job.key == "cfo" else []))
			with _as(member):
				set_eligibility(app.name, 1 if eligible else 0, reason)
			app.eligible = eligible

	def score(self, job):
		from pathways.api.scoring import get_rubric_for_job_opening, submit_shortlisting_score

		_when, take, share = job.spec["scoring"]
		rubric = get_rubric_for_job_opening(job.name, "Shortlisting")
		pool = sorted([a for a in self._live(job) if a.get("eligible")], key=lambda a: -a.who.strength)
		pool = pool[: max(1, round(len(pool) * share))] if share < 1 else pool
		for rank, app in enumerate(pool):
			shortlist = rank < take
			criteria = []
			if rubric and rubric["criteria"] and rubric["scoring_mode"] != "Pass/Fail Only":
				for c in rubric["criteria"]:
					top = float(c["max_score"])
					criteria.append({"criterion_label": c["criterion_label"], "max_score": top, "score_given": round(min(top, max(0, top * (0.35 + 0.6 * app.who.strength + self.rng.uniform(-0.08, 0.08)))) * 2) / 2})
			remarks = self.rng.choice(SHORTLIST_YES if shortlist else SHORTLIST_NO)
			member = self.s(job.committee_members[rank % len(job.committee_members)])
			with _as(member):
				submit_shortlisting_score(app.name, job.committee, 1 if shortlist else 0, remarks, criteria)
			app.shortlisted = shortlist

	def shortlisting_regrets(self, job):
		from pathways.api.scoring import send_regret_emails

		with _as(self.s(job.raiser)):
			send_regret_emails(job.name)

	def _shortlisted(self, job):
		return sorted([a for a in self._live(job) if a.get("shortlisted")], key=lambda a: -a.who.strength)

	# ------------------------------------------------------------ HR interaction (Round 1)

	def schedule_hr(self, job):
		from pathways.api.interviews import schedule_interviews

		_on, interview_at, assessors, _assessed = job.spec["hr"]
		apps = self._shortlisted(job)
		with _as(self.s(job.raiser)):
			res = schedule_interviews(
				job.name, [a.name for a in apps], "HR Interaction", str(interview_at), slot_minutes=30,
				mode="Video Conference", meeting_link=meet_link(self.rng), meeting_platform="Google Meet",
				rsvp_deadline=str(add_days(interview_at, -1)), send_invite=1, hr_assessors=[self.s(a) for a in assessors],
			)
		for app, iv in zip(apps, res["interviews"]):
			app.hr_interview = iv

	def rsvp(self, job, round_type, partial):
		from pathways.api.interviews import respond_rsvp

		field = "hr_interview" if round_type == "HR Interaction" else "final_interview"
		apps = [a for a in self._live(job) if a.get(field)]
		for i, app in enumerate(apps):
			if partial and i == len(apps) - 1:
				continue  # still to reply
			response = "Declined" if job.spec.get("rsvp_decline") and round_type == "Final" and i == len(apps) - 1 else "Confirmed"
			with _as(app.who.email):
				respond_rsvp(app.get(field), response)
			app.declined = response == "Declined"

	def assess_hr(self, job):
		from pathways.api.interviews import set_interview_status
		from pathways.api.panel import get_assessment_form, submit_assessment

		_on, _at, assessors, _assessed = job.spec["hr"]
		apps = self._shortlisted(job)
		for rank, app in enumerate(apps):
			strength = app.who.strength
			# The weakest of the round is not recommended, the next is on hold.
			outcome = "Not recommended" if rank == len(apps) - 1 else ("Hold" if rank == len(apps) - 2 else "Recommend for final")
			app.hr_outcome = outcome
			for key in assessors:
				with _as(self.s(key)):
					form = get_assessment_form(app.hr_interview)
					scores = self._scores(form, strength)
					submit_assessment(
						app.hr_interview, scores, additional_comments=self.rng.choice(HR_NOTES[outcome]),
						hr_outcome=outcome, expected_salary=expected_pay(job, app.who), notice_period=self.rng.choice(["30 days", "60 days", "90 days", "Immediate"]),
						signature=signature_png(self.s(key)),
					)
			with _as(self.s(job.raiser)):
				set_interview_status(app.hr_interview, "Completed")

	def _scores(self, form, strength):
		scores = {}
		for c in form["rubric"]["criteria"]:
			top = float(c["max_score"])
			scores[c["label"]] = round(min(top, max(0, top * (0.3 + 0.65 * strength + self.rng.uniform(-0.1, 0.1)))) * 2) / 2
		return scores

	def final_shortlist(self, job):
		from pathways.api.interviews import save_shortlisting_note, set_final_shortlist
		from pathways.api.panel import set_selection_outcome

		apps = self._shortlisted(job)
		chosen = [a for a in apps if a.hr_outcome != "Not recommended"]
		dropped = [a for a in apps if a.hr_outcome == "Not recommended"]
		with _as(self.s(job.raiser)):
			set_final_shortlist(job.name, [a.name for a in chosen], 1, "Recommended after the HR interaction.")
			if dropped:
				set_selection_outcome([a.name for a in dropped], "Not Selected")
			save_shortlisting_note(
				job.name,
				note=shortlisting_note_html(job, len(self._live(job)), len(apps), len(chosen)),
				prepared_by=self.s(job.raiser),
			)
		for a in chosen:
			a.final_listed = True
		for a in dropped:
			a.dropped = True

	# ------------------------------------------------------------ final interview

	def selection_committee(self, job):
		from pathways.api.interviews import save_selection_committee

		_on, members, interview_at = job.spec["panel"]
		rows = [{"member": self.s(m), "designation_label": STAFF[m][2], "is_external_expert": 1 if m in EXTERNAL else 0} for m in members]
		with _as(self.s(job.raiser)):
			save_selection_committee(job.name, rows, scheduled_date=str(getdate(interview_at)), scheduled_time=interview_at.strftime("%H:%M:%S"))
		job.panel = members

	def _final_pool(self, job):
		if job.spec.get("hr"):
			return [a for a in self._shortlisted(job) if a.get("final_listed")]
		return self._shortlisted(job)

	def schedule_final(self, job):
		from pathways.api.interviews import schedule_interviews

		_on, mode, slot, _assessed, _share = job.spec["final"]
		interview_at = job.spec["panel"][2]
		apps = self._final_pool(job)
		kwargs = {"location": "Board Room, Administrative Block, NLSIU, Nagarbhavi, Bengaluru"} if mode == "In-Person" else {"meeting_link": meet_link(self.rng), "meeting_platform": "Google Meet"}
		with _as(self.s(job.raiser)):
			res = schedule_interviews(
				job.name, [a.name for a in apps], "Final", str(interview_at), slot_minutes=slot, mode=mode,
				rsvp_deadline=str(add_days(interview_at, -2)), send_invite=1, **kwargs,
			)
		for app, iv in zip(apps, res["interviews"]):
			app.final_interview = iv

	def assess_final(self, job):
		from pathways.api.interviews import set_interview_status
		from pathways.api.panel import get_assessment_form, submit_assessment

		share = job.spec["final"][4]
		apps = [a for a in self._final_pool(job) if a.get("final_interview")]
		declined = [a for a in apps if a.get("declined")]
		for app in declined:
			with _as(self.s(job.raiser)):
				set_interview_status(app.final_interview, "Cancelled", reason="Candidate informed us they have accepted another offer.", notify=1)
			app.cancelled = True
		apps = [a for a in apps if not a.get("declined")]
		order = sorted(apps, key=lambda a: -a.who.strength)
		levels = ("Recommended", "Waitlist", "Not Recommended")
		for n, app in enumerate(apps):
			rank = order.index(app)
			level = 0 if rank < job.vacancies else (1 if rank == job.vacancies else 2)
			strength = app.who.strength
			panel = job.panel if (share >= 1 or n < len(apps) * share) else job.panel[:-1]
			for key in panel:
				with _as(self.s(key)):
					form = get_assessment_form(app.final_interview)
					scores = self._scores(form, strength)
					# Panellists mostly agree; now and then one is a step apart.
					shift = self.rng.choice([-1, 1]) if self.rng.random() < 0.2 else 0
					verdict = levels[min(2, max(0, level + shift))]
					submit_assessment(
						app.final_interview, scores, verdict=verdict, additional_comments=self.rng.choice(FINAL_NOTES[verdict]),
						area_of_specialization=self.rng.choice(FAMILIES[job.family]["spec"]) if job.track == "Faculty" else None,
						signature=signature_png(self.s(key)),
					)
			with _as(self.s(job.raiser)):
				set_interview_status(app.final_interview, "Completed")

	def record_outcomes(self, job):
		from pathways.api.panel import set_selection_outcome

		apps = [a for a in self._final_pool(job) if a.get("final_interview") and not a.get("cancelled")]
		apps.sort(key=lambda a: -a.who.strength)
		selected = apps[: job.vacancies]
		waitlisted = apps[job.vacancies : job.vacancies + 1]
		rest = apps[job.vacancies + 1 :]
		with _as(self.s(job.raiser)):
			set_selection_outcome([a.name for a in selected], "Selected")
			if waitlisted:
				set_selection_outcome([a.name for a in waitlisted], "Waitlisted")
			if rest:
				set_selection_outcome([a.name for a in rest], "Not Selected")
		job.selected, job.waitlisted = selected, waitlisted

	# ------------------------------------------------------------ references, regrets, panel

	def request_references(self, job):
		from pathways.api.reference_checks import create_checks, send_request

		for app in job.selected:
			with _as(self.s(job.raiser)):
				app.checks = create_checks(app.name)["created"]
				if job.spec["references"][2] == "first" and app is not job.selected[0]:
					send_request(app.checks[0])

	def record_references(self, job):
		from pathways.api.reference_checks import record_responses

		for app in job.selected:
			if job.spec["references"][2] == "first" and app is not job.selected[0]:
				continue
			for check in app.checks:
				doc = frappe.get_doc("Reference Check", check)
				answers = {row.name: reference_answer(row, app.who, self.rng) for row in doc.responses}
				with _as(self.s(job.raiser)):
					record_responses(check, answers, f"Both referees spoke very positively of {app.who.first}; no concerns raised about integrity or conduct. Recommended.", complete=1)

	def post_interview_regrets(self, job, include_waitlisted):
		from pathways.api.selection import send_post_interview_regrets

		with _as(self.s(job.raiser)):
			send_post_interview_regrets(job.name, include_waitlisted=include_waitlisted)

	def panel_thanks(self, job, amount):
		from pathways.api.honorarium import send_panel_thanks, update_honorarium

		with _as(self.s(job.raiser)):
			send_panel_thanks(job.name)
			for row in frappe.get_all("Panel Honorarium", {"job_opening": job.name, "is_external": 1}, ["name", "panellist"]):
				update_honorarium(row.name, amount=amount, pan_number=fake_pan(self.rng, row.panellist), remarks="Honorarium for serving as external expert on the Selection Committee.")

	def approve_honoraria(self, job):
		from pathways.api.honorarium import approve

		names = frappe.get_all("Panel Honorarium", {"job_opening": job.name, "status": "Pending"}, pluck="name")
		with _as(self.s("lakshmi")):
			approve(names)

	def pay_honoraria(self, job):
		from pathways.api.honorarium import mark_paid

		names = frappe.get_all("Panel Honorarium", {"job_opening": job.name, "status": "Approved"}, pluck="name")
		with _as(self.s("sanjana")):
			mark_paid(names, payment_reference=f"NEFT/{frappe.utils.today().replace('-', '')}/{self.rng.randint(100000, 999999)}")

	# ------------------------------------------------------------ selection green sheet

	def raise_post_gs(self, job, which):
		from pathways.api.post_green_sheet import create_from_outcomes, save_sheet

		recommended = job.selected[which]
		waitlist = job.waitlisted[0] if (job.waitlisted and which == 0) else None
		pay = expected_pay_number(job, recommended.who)
		with _as(self.s(job.raiser)):
			name = create_from_outcomes(job.name)
			sheet = frappe.get_doc("Post-Interview Green Sheet", name)
			rows = []
			for row in sheet.compensation_table:
				who = next((a.who for a in job.selected if a.name == row.application), recommended.who)
				rows.append({**{k: row.get(k) for k in ("application", "candidate_name", "years_experience", "highest_qualification", "position_offered", "medical_insurance", "leave_applicable")}, "recommended_salary": expected_pay_number(job, who)})
			data = {
				"subject": f"Selection of candidate for the post of {job.title}",
				"file_reference": f"NLSIU/PNC/REC/2026/{self.rng.randint(100, 399)}",
				"recommended_application": recommended.name,
				"waitlist_application": waitlist.name if waitlist else None,
				"verbal_acceptance": 1,
				"reference_check_status": "Satisfactory" if job.spec["references"][2] == "all" or which == 0 else "Initiated",
				"date_of_appointment": "On or before " + frappe.utils.formatdate(add_days(frappe.utils.today(), 40), "dd.MM.yyyy"),
				"duration_of_appointment": TENURE.get(frappe.db.get_value("Job Opening", job.name, "employment_type")),
				"reports_to": REPORTS_TO.get(job.position, "Registrar"),
				"probation_period": "Two years" if job.track == "Faculty" else "One year",
				"advertised_pay_level": frappe.db.get_value("Job Opening", job.name, "pay_level"),
				"fixed_pay_level": frappe.db.get_value("Job Opening", job.name, "pay_level"),
				"gross_salary": pay,
				"ctc": round(pay * 12 * 1.12, -3),
				"current_gross_salary": round(pay * 0.85, -2),
				"pay_fixation_note": "Pay fixed at the entry level of the advertised pay level, with increments for relevant experience as per University norms.",
				"compensation_table": rows,
			}
			if job.track == "Research":
				data.update({"project_name": "Women's Inclusion and Leadership in Law (WILL) Initiative", "funding_source": "NVF Grant 2026"})
			score_sheet = save_file(f"Consolidated-Score-Sheet-{_slug(job.title)}.pdf", make_pdf("Consolidated Score Sheet", [job.title, "Scores of all panellists for every candidate interviewed; average against the 50% bar."]), ("Post-Interview Green Sheet", name))
			data["score_sheet_attachment"] = score_sheet.file_url
			save_sheet(name, data, submit=1)
		job.setdefault("post_gs", {})[which] = name

	def approve_post_gs(self, job, which, _i):
		self._approve("Post-Interview Green Sheet", job.post_gs[which], APPROVAL_REMARKS)

	# ------------------------------------------------------------ offer

	def _offer_app(self, job, i):
		return job.selected[i]

	def offer_create(self, job, i):
		from pathways.api.offer import create_offer

		app = self._offer_app(job, i)
		employment = frappe.db.get_value("Job Opening", job.name, "employment_type")
		pay = expected_pay_number(job, app.who)
		doj = job.spec["offers"][i].get("respond", (None, None, None))[2] or str(add_days(frappe.utils.today(), 30))
		data = {
			"proposed_doj": doj,
			"place_of_posting": "NLSIU, Nagarbhavi, Bengaluru",
			"reporting_to": REPORTS_TO.get(job.position, "Registrar"),
			"probation_period": "one year" if job.track != "Faculty" else "two years",
			"verbal_offer_date": str(add_days(frappe.utils.today(), -2)),
			"verbal_offer_by": self.s("meera"),
			"verbal_offer_compensation": f"Rs {pay:,.0f} gross per month",
			"verbal_offer_notes": f"{app.who.first} confirmed interest on the call and can join by the proposed date.",
			"reference_number": f"NLSIU/PNC/AO/2026/{self.rng.randint(200, 499)}",
		}
		if employment in ("Consultant",):
			data["consolidated_fee"] = pay
			data["contract_period"] = "One year, renewable on performance"
		else:
			data["gross_monthly_salary"] = pay
			data["pay_level"] = frappe.db.get_value("Job Opening", job.name, "pay_level") or PAY.get(job.position)
		if employment == "Contract":
			data["contract_period"] = "Two years"
		with _as(self.s(job.raiser)):
			app.offer = create_offer(app.name, data)

	def offer_review(self, job, i):
		from pathways.api.offer import submit_for_review, update_offer

		app = self._offer_app(job, i)
		with _as(self.s(job.raiser)):
			if frappe.db.get_value("Offer Appointment Order", app.offer, "review_remarks"):
				update_offer(app.offer, {"probation_period": "two years"})
			submit_for_review(app.offer)

	def offer_return(self, job, i, remarks):
		from pathways.api.offer import return_offer

		with _as(self.s("shalini")):
			return_offer(self._offer_app(job, i).offer, remarks)

	def offer_approve(self, job, i):
		from pathways.api.offer import approve_offer

		with _as(self.s("shalini")):
			approve_offer(self._offer_app(job, i).offer, "Checked against the approved green sheet and pay scales.")

	def offer_sign(self, job, i):
		from pathways.api.offer import sign_offer

		with _as(self.s("sudha")):
			sign_offer(self._offer_app(job, i).offer, signature=signature_png(self.s("sudha")))

	def offer_send(self, job, i):
		from pathways.api.offer import send_offer

		with _as(self.s(job.raiser)):
			send_offer(self._offer_app(job, i).offer)

	def offer_respond(self, job, i):
		from pathways.api.offer import respond_to_offer

		app = self._offer_app(job, i)
		_when, response, doj = job.spec["offers"][i]["respond"]
		with _as(app.who.email):
			signed = save_file(f"Signed-Appointment-Order-{_slug(app.who.full_name)}.pdf", make_pdf("Appointment Order (signed copy)", [f"Accepted and signed by {app.who.full_name}", f"Date of joining: {doj}"]))
			respond_to_offer(app.offer, response, confirmed_doj=doj, signed_copy_attachment=signed.file_url)
		job.joiner = app

	# ------------------------------------------------------------ onboarding

	def _collection(self, job):
		return frappe.get_doc("Document Collection", {"application": job.joiner.name})

	def upload_documents(self, job, start, end):
		from pathways.api.documents import upload_document

		who = job.joiner.who
		doc = self._collection(job)
		rows = [r for r in doc.checklist if r.requirement == "Mandatory" or self.rng.random() < 0.4]
		if job.spec["onboarding"].get("partial"):
			rows = rows[: max(3, len(rows) * 2 // 3)]
		with _as(who.email):
			for row in rows:
				name, content = onboarding_file(row.document_type, who)
				file = save_file(name, content)
				upload_document(doc.name, row.document_type, file.file_url)

	def verify_documents(self, job):
		from pathways.api.documents import verify_document

		doc = self._collection(job)
		partial = job.spec["onboarding"].get("partial")
		with _as(self.s("shalini")):
			for row in doc.checklist:
				if not row.attachment or row.status == "Verified":
					continue
				if partial and row.document_type == "Relieving Letter":
					verify_document(doc.name, row.document_type, False, "The relieving letter is unsigned. Please upload the copy signed by your current employer.")
				elif partial and self.rng.random() < 0.4:
					continue  # still to be checked
				else:
					verify_document(doc.name, row.document_type, True)

	def confirm_joining(self, job):
		from pathways.api.joining import set_status

		name = frappe.db.get_value("Joining", {"application": job.joiner.name}, "name")
		with _as(self.s(job.raiser)):
			set_status(name, "Confirmed", {"reporting_manager": REPORTS_TO.get(job.position, "Registrar")})
		job.joining = name

	def it_progress(self, job):
		from pathways.api.it_requests import save_request

		request = frappe.db.get_value("Joining", job.joining, "it_facilities_request")
		with _as(self.s("manoj")):
			save_request(request, {"laptop_arranged": 1, "remarks": "Dell Latitude 5440 issued from stock; asset tag NLS-IT-" + str(self.rng.randint(1000, 9999))})

	def it_complete(self, job):
		from pathways.api.it_requests import save_request

		who = job.joiner.who
		request = frappe.db.get_value("Joining", job.joining, "it_facilities_request")
		with _as(self.s("manoj")):
			save_request(
				request,
				{"laptop_arranged": 1, "official_email_created": 1, "official_email": f"{who.first}.{who.last}@nls.ac.in".lower().replace("'", ""), "access_card_issued": 1, "seating_arranged": 1},
				complete=True,
			)

	def mark_joined(self, job):
		from pathways.api.joining import set_status

		with _as(self.s(job.raiser)):
			set_status(job.joining, "Joined")

	def fill_job(self, job):
		from pathways.api.job_opening import update_job_opening

		with _as(self.s(job.raiser)):
			update_job_opening(job.name, {"status": "Filled"})


# ===================================================================== application form


class ApplicationForm:
	"""The apply page's payload for one person, uploads included."""

	def __init__(self, demo, job, job_doc, who, user):
		from pathways.utils.application_form import _form_options, get_form_sections, get_required_documents

		self.demo, self.rng, self.job, self.doc, self.who, self.user = demo, demo.rng, job, job_doc, who, user
		self.sections = get_form_sections(job_doc)
		self.options = _form_options(job_doc)
		self.required = get_required_documents(job_doc)
		self.family = FAMILIES[job.family]
		self.tokens = {}

	def upload(self, label, content=None, ext="pdf"):
		from pathways.utils.application_form import sign_upload

		who = self.who
		content = content or make_pdf(
			label,
			[
				who.full_name,
				who.email,
				f"Prepared for the application to {self.job.title}",
				f"Reference {frappe.generate_hash(length=10)}",
			],
		)
		file = save_file(f"{_slug(who.full_name)}-{_slug(label)}.{ext}", content)
		if self.user == "Guest":
			self.tokens[file.file_url] = sign_upload(file.name)
		return file.file_url

	def build(self):
		who, rng, fam = self.who, self.rng, self.family
		today = getdate(frappe.utils.today())
		strong = who.strength
		pg_year = min(who.dob.year + 23 + rng.randint(0, 1), today.year - 1)
		grad_year = pg_year - 2
		institutions = self.options.get("institutions") or fam["inst"]

		def pct(base):
			return f"{min(92, max(48, base + 30 * strong + rng.uniform(-4, 4))):.1f}"

		quals = [
			{
				"degree_level": "Undergraduate",
				"degree_name": rng.choice(fam["ug"]),
				"other_institution": rng.choice(institutions),
				"year_of_graduation": grad_year,
				"percentage_or_cgpa": pct(52),
				"division_grade": "First Class with Distinction" if strong > 0.75 else ("First Class" if strong > 0.35 else "Second Class"),
				"specialization": rng.choice(fam["spec"]),
				"transcript_attachment": self.upload("UG Transcript"),
				"certificate_attachment": self.upload("UG Degree Certificate"),
			}
		]
		has_pg = self.doc.require_postgraduate or rng.random() < 0.7
		if has_pg:
			p = pct(50)
			quals.append(
				{
					"degree_level": "Postgraduate",
					"degree_name": rng.choice(fam["pg"]),
					"other_institution": rng.choice(institutions),
					"year_of_graduation": pg_year,
					"percentage_or_cgpa": p,
					"cgpa": f"{float(p) / 10 + 0.3:.2f}" if rng.random() < 0.5 else None,
					"cgpa_scale": "10" if rng.random() < 0.5 else None,
					"division_grade": "First Class" if float(p) >= 60 else "Second Class",
					"specialization": rng.choice(fam["spec"]),
					"transcript_attachment": self.upload("PG Transcript"),
					"certificate_attachment": self.upload("PG Degree Certificate"),
				}
			)
			if not (quals[-1]["cgpa"] and quals[-1]["cgpa_scale"]):
				quals[-1]["cgpa"] = quals[-1]["cgpa_scale"] = None

		months_total = max(0, who.seniority * 12 + rng.randint(-5, 5))
		employment = self.employment(months_total, today)
		app = {
			"qualifications": quals,
			"employment_history": employment,
			"notice_period": rng.choice(["30 days", "60 days", "90 days", "One month", "Three months"]) if employment else None,
			"screening_answers": self.screening(),
			"references": self.references(),
			"source": rng.choice(frappe.get_all("Candidate Source", {"is_active": 1}, pluck="name")),
			"current_salary": current_pay(self.job, who) if employment else 0,
			"expected_salary": expected_pay_number(self.job, who),
			"earliest_doj": str(add_days(today, rng.choice([30, 45, 60, 90]))),
			"resume_attachment": self.upload("Curriculum Vitae", make_pdf(f"Curriculum Vitae - {who.full_name}", cv_lines(who, quals, employment))),
			"sop_attachment": self.upload("Statement of Purpose", make_pdf("Statement of Purpose", sop_lines(who, self.job))),
			"documents": self.documents(),
		}
		if self.sections["experience_months"]:
			teaching = min(months_total, int(months_total * (0.6 + 0.3 * rng.random())))
			app.update(
				{
					"overall_experience_months": months_total,
					"teaching_experience_months": teaching,
					"research_experience_months": int(months_total * 0.5),
					"legal_experience_months": int(months_total * 0.2) if self.job.family == "law" else 0,
					"legal_experience_details": "Litigation assistance and legal aid clinic work." if self.job.family == "law" else "",
				}
			)
		else:
			overall = round(months_total / 12, 1)
			app.update({"overall_experience_years": overall, "relevant_experience_years": round(overall * (0.6 + 0.35 * rng.random()), 1)})
		app.update(self.academic(quals, grad_year, pg_year))

		candidate = {
			"full_name": who.full_name,
			"email": who.email,
			"mobile_number": who.mobile,
			"date_of_birth": str(who.dob),
			"gender": who.gender,
			"address": who.address,
		}
		if self.sections["category_disability"]:
			candidate["category"] = who.category
		return {"candidate": candidate, "application": app, "declaration_accepted": 1, "upload_tokens": self.tokens}

	def employment(self, months_total, today):
		rng, fam = self.rng, self.family
		if months_total <= 0:
			return []
		jobs, end = [], today
		remaining = months_total
		teaching = self.job.track == "Faculty"
		while remaining > 0 and len(jobs) < 3:
			span = remaining if len(jobs) == 2 else min(remaining, rng.randint(18, 60))
			start = add_days(end, -int(span * 30.4))
			roles = fam.get("teaching_roles") if teaching and fam.get("teaching_roles") else fam["roles"]
			jobs.append(
				{
					"designation": rng.choice(roles),
					"employer_name": rng.choice(fam["employers"]),
					"from_date": str(start),
					"to_date": None if not jobs else str(end),
					"is_current": 0 if jobs else 1,
					"key_responsibilities": fam["duties"],
				}
			)
			end = add_days(start, -rng.randint(10, 60))
			remaining -= span
		return jobs

	def screening(self):
		answers, previous = [], None
		for q in self.doc.screening_questions or []:
			if q.show_if_previous_answer and previous != q.show_if_previous_answer:
				previous = ""
				continue
			if q.answer_type == "Yes/No":
				answer = "Yes" if self.who.strength >= 0.25 or self.rng.random() < 0.3 else "No"
			elif q.answer_type == "Single Choice":
				answer = self.rng.choice([o.strip() for o in (q.options or "").splitlines() if o.strip()])
			elif q.answer_type == "Number":
				answer = str(self.who.seniority)
			else:
				answer = "Yes, as described in my CV."
			row = {"idx": q.idx, "answer": answer}
			if q.answer_type == "Yes/No" and q.ask_details_if_yes and answer == "Yes":
				row["details"] = f"{self.who.seniority} years in comparable roles; details in the CV and experience certificates."
			answers.append(row)
			previous = answer
		return answers

	def references(self):
		rng = self.rng
		relations = self.options["referee_relationships"]
		refs = []
		for i in range(2):
			first, last = rng.choice(FEMALE + MALE), rng.choice(LAST)
			refs.append(
				{
					"referee_name": f"{'Prof. ' if self.job.track == 'Faculty' else ''}{first} {last}",
					"current_designation_org": f"{rng.choice(self.family['roles'])}, {rng.choice(self.family['employers'])}",
					"relationship": relations[i % len(relations)] if i == 0 else rng.choice(relations[1:]),
					"email": f"{first}.{last}.ref{rng.randint(10, 99)}@{DOMAIN}".lower().replace("'", ""),
					"mobile": self.demo._mobile(),
				}
			)
			self.demo._unsubscribe(refs[-1]["email"])
		return refs

	def documents(self):
		rows = []
		for spec in self.required:
			if not spec["mandatory"] and self.rng.random() < 0.6:
				continue
			ext = "pdf" if "pdf" in spec["formats"] else spec["formats"][0]
			content = None if ext == "pdf" else (photo_png(self.who.seq) if ext in ("png",) else make_docx([spec["label"], self.who.full_name]))
			if ext in ("jpg", "jpeg"):
				ext, content = "png", photo_png(self.who.seq)
			rows.append({"document_type": spec["document_type"], "attachment": self.upload(spec["label"], content, ext)})
		return rows

	def academic(self, quals, grad_year, pg_year):
		rng, who, out = self.rng, self.who, {}
		s = self.sections
		if s["specialization"]:
			options = self.options.get("specializations") or []
			out["specializations"] = rng.sample(options, k=min(len(options), rng.randint(1, 3))) if options else []
			out["other_specialization"] = "" if options else rng.choice(self.family["spec"])
		if s["category_disability"]:
			if who.seq % 23 == 5:
				out.update({"disability_type": self.options["disability_types"][1], "disability_percentage": 45})
			else:
				out["disability_type"] = ""
		if s["phd"]:
			awarded = "Yes" if who.strength >= 0.45 or who.seniority >= 8 else "No"
			out["phd_awarded"] = awarded
			if awarded == "Yes":
				quals.append(
					{
						"degree_level": "Doctoral",
						"degree_name": self.family.get("phd", "Ph.D."),
						"other_institution": rng.choice(self.options.get("institutions") or self.family["inst"]),
						"year_of_graduation": min(getdate(frappe.utils.today()).year, pg_year + 4 + rng.randint(0, 2)),
						"specialization": rng.choice(self.family["spec"]),
						"qs_rank": rng.choice([None, rng.randint(150, 900)]),
						"certificate_attachment": self.upload("PhD Certificate"),
					}
				)
		if s["net"]:
			qualified = "Yes" if who.strength >= 0.3 else "No"
			out["net_qualified"] = qualified
			if qualified == "Yes":
				subjects = self.options.get("net_subjects") or []
				wanted = "Law" if self.job.family == "law" else rng.choice(["Economics", "Sociology", "Political Science"])
				match = next((x for x in subjects if wanted.lower() in x.lower()), subjects[0] if subjects else "")
				out.update(
					{
						"net_exam": rng.choice(["NET", "NET", "SET"]),
						"net_subject": match,
						"net_award_date": f"{min(getdate(frappe.utils.today()).year - 1, pg_year + 1)}-{rng.choice(['01', '06', '12'])}-15",
						"net_roll_number": f"{rng.choice(['KA', 'DL', 'TN', 'MH'])}{rng.randint(10000000, 99999999)}",
					}
				)
		if s["admin_responsibilities"]:
			held = "Yes" if who.seniority >= 5 else "No"
			out["held_admin_responsibility"] = held
			if held == "Yes":
				kinds = self.options["admin_responsibility_types"]
				out["administrative_responsibilities"] = [
					{"responsibility_type": kinds[0], "duration_months": rng.randint(12, 36), "details": "Member, Academic Council and hostel warden."},
					{"responsibility_type": kinds[1], "duration_months": rng.randint(12, 24), "details": "Convenor, Moot Court Committee."},
				][: 1 + (who.seniority >= 9)]
		if s["publications"]:
			count = max(s["min_publications"], min(s["max_publications"], 1 + int(who.strength * 3)))
			out["publications"] = [
				{
					"title": rng.choice(PUBLICATION_TITLES[self.job.family]),
					"journal_name": rng.choice(JOURNALS[self.job.family]),
					"volume": f"Vol. {rng.randint(8, 34)}({rng.randint(1, 4)})",
					"doi_link": f"https://doi.org/10.{rng.randint(1000, 9999)}/{frappe.generate_hash(length=8)}",
					"pdf_attachment": self.upload(f"Publication {i + 1}"),
				}
				for i in range(count)
			]
		return out


# ===================================================================== content


PAY = {
	"ADM-CFO": "Level 14 (VII CPC)",
	"ADM-MGR-PACE": "Level 10 (VII CPC)",
	"RES-PD-WILL": "Rs. 1,50,000 - 1,80,000 per month (consolidated)",
	"RES-RA-WILL": "Rs. 55,000 - 65,000 per month (consolidated)",
}
BASE_PAY = {
	"ADM-CFO": 235000, "ADM-AM-PNC": 72000, "ADM-AM-FIN": 72000, "ADM-MGR-PACE": 118000, "ADM-GD": 60000,
	"FAC-ASSOC-LAW": 205000, "FAC-ASSOC-HSS": 205000, "FAC-AP-LAW-2Y": 110000, "FAC-AP-SS-2Y": 110000,
	"RES-PD-WILL": 165000, "RES-RA-WILL": 60000,
}
TENURE = {
	"Permanent": "Permanent, until the age of superannuation, subject to a probation period.",
	"Contract": "Two years on contract, renewable on performance review.",
	"Consultant": "One year on consultancy, renewable on performance and funding.",
	"Grant-funded": "For the duration of the grant.",
}
REPORTS_TO = {
	"ADM-CFO": "Vice Chancellor",
	"ADM-AM-PNC": "Director - People and Culture",
	"ADM-AM-FIN": "Chief Finance Officer",
	"ADM-MGR-PACE": "Director - PACE",
	"ADM-GD": "Manager - Communications",
	"FAC-ASSOC-LAW": "Dean - Academics",
	"FAC-ASSOC-HSS": "Dean - Academics",
	"FAC-AP-LAW-2Y": "Dean - Academics",
	"FAC-AP-SS-2Y": "Dean - Academics",
	"RES-PD-WILL": "Director, CSLP",
	"RES-RA-WILL": "Project Director - WILL Initiative",
}
APPROVAL_REMARKS = [
	"Approved.",
	"Approved as proposed.",
	"Recommended for approval.",
	"Approved. Budget provision confirmed.",
	"Seen and approved.",
	"Approved; please proceed.",
]
SHORTLIST_YES = [
	"Strong academic record and directly relevant experience.",
	"Meets all criteria; experience in a comparable institution.",
	"Shortlisted: good fit with the role's requirements.",
	"Relevant experience and a well-argued statement of purpose.",
]
SHORTLIST_NO = [
	"Eligible, but other candidates have more relevant experience.",
	"Experience is mostly outside the higher education sector.",
	"Not shortlisted under the 1:5 ratio.",
	"Statement of purpose does not address the role.",
]
HR_NOTES = {
	"Recommend for final": ["Clear communicator; well prepared and understands the role.", "Good motivation and relevant experience; recommend for the final round."],
	"Hold": ["Adequate, but salary expectation is above the advertised range.", "Relevant experience; some gaps in stakeholder management."],
	"Not recommended": ["Limited understanding of the role and its context.", "Experience does not match the responsibilities of the post."],
}
FINAL_NOTES = {
	"Recommended": ["Excellent grasp of the domain and thoughtful answers. Recommended for appointment.", "Strong candidate; clear vision for the role."],
	"Waitlist": ["Good candidate; may be considered if the first choice does not join.", "Competent and well prepared; keep on the waitlist."],
	"Not Recommended": ["Answers lacked depth on core areas of the post.", "Not suitable for the post at present."],
}
PUBLICATION_TITLES = {
	"law": [
		"Judicial Review of Delegated Legislation in India", "The Basic Structure Doctrine after Fifty Years",
		"Bail Jurisprudence and Undertrial Detention", "Women in the Indian Legal Profession: Entry and Retention",
		"Data Protection and the Right to Privacy", "Arbitration and Public Policy in Indian Courts",
	],
	"ss": [
		"Caste, Class and Access to Higher Education", "Informal Labour and Urban Governance in Bengaluru",
		"Federalism and Fiscal Transfers in India", "Social Movements and Legal Mobilisation",
		"Gender and Unpaid Care Work in Rural Karnataka",
	],
}
PUBLICATION_TITLES.update({k: PUBLICATION_TITLES["ss"] for k in ("finance", "hr", "pace", "design")})
JOURNALS = {
	"law": ["Indian Law Review", "NLSIU Law Review", "Journal of the Indian Law Institute", "Socio-Legal Review", "Asian Journal of Comparative Law"],
	"ss": ["Economic and Political Weekly", "Contributions to Indian Sociology", "Indian Economic Review", "Studies in Indian Politics"],
}
JOURNALS.update({k: JOURNALS["ss"] for k in ("finance", "hr", "pace", "design")})


def meet_link(rng):
	letters = "abcdefghijklmnopqrstuvwxyz"
	part = lambda n: "".join(rng.choice(letters) for _ in range(n))  # noqa: E731
	return f"https://meet.google.com/{part(3)}-{part(4)}-{part(3)}"


def fake_pan(rng, seed):
	letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	return "".join(rng.choice(letters) for _ in range(3)) + "P" + seed[0].upper() + f"{rng.randint(1000, 9999)}" + rng.choice(letters)


def expected_pay_number(job, who):
	base = BASE_PAY.get(job.position, 80000)
	return round(base * (0.92 + 0.2 * who.strength) / 1000) * 1000


def expected_pay(job, who):
	return f"Rs {expected_pay_number(job, who):,} per month"


def current_pay(job, who):
	return round(expected_pay_number(job, who) * (0.72 + 0.12 * who.strength) / 500) * 500


def jd_html(job, position):
	return (
		f"<p>The National Law School of India University, Bengaluru invites applications for the post of <b>{job.title}</b> "
		f"in the {position.department} department.</p>"
		"<p><b>Key responsibilities</b></p><ul>"
		+ "".join(f"<li>{r}</li>" for r in RESPONSIBILITIES.get(job.family, RESPONSIBILITIES["finance"]))
		+ "</ul><p><b>Desired profile</b></p><ul>"
		+ "".join(f"<li>{r}</li>" for r in PROFILE.get(job.family, PROFILE["finance"]))
		+ "</ul><p>NLSIU is an equal opportunity employer and encourages applications from women, persons with disabilities and members of under-represented groups.</p>"
	)


def jd_lines(job, position):
	return [
		f"Department: {position.department}",
		f"Employment type: {position.employment_type}",
		f"Vacancies: {job.vacancies}",
		"",
		"Key responsibilities:",
		*[f"  - {r}" for r in RESPONSIBILITIES.get(job.family, RESPONSIBILITIES["finance"])],
		"",
		"Desired profile:",
		*[f"  - {r}" for r in PROFILE.get(job.family, PROFILE["finance"])],
	]


RESPONSIBILITIES = {
	"finance": ["Lead the finance and accounts function, budgeting and fund management.", "Ensure statutory compliance (GST, TDS, PF) and coordinate audits.", "Report to the Finance Committee and the Executive Council."],
	"hr": ["Run end-to-end recruitment for academic and non-academic posts.", "Maintain HRMS records and coordinate onboarding.", "Support policy implementation and employee engagement."],
	"pace": ["Manage operations of distance and executive education programmes.", "Coordinate admissions, examinations and learner support.", "Manage vendors, platforms and programme budgets."],
	"design": ["Design print and digital collateral for the University.", "Lay out reports, books and event material.", "Maintain brand consistency across channels."],
	"law": ["Teach courses in the undergraduate and postgraduate law programmes.", "Undertake research and publish in peer-reviewed journals.", "Contribute to the academic and institutional life of the University."],
	"ss": ["Teach social science courses in the integrated law programme.", "Supervise research and dissertations.", "Undertake research and publish in peer-reviewed journals."],
}
PROFILE = {
	"finance": ["CA / CMA with relevant post-qualification experience.", "Experience in a university or large non-profit is an advantage."],
	"hr": ["Master's degree in HR or a related field with at least 55% marks.", "4+ years of relevant experience; familiarity with academic recruitment."],
	"pace": ["Post-graduate degree with 7-10 years in programme operations.", "Experience with distance education is preferred."],
	"design": ["Degree in design or fine arts with a strong portfolio.", "Proficiency in Adobe Creative Suite and Figma."],
	"law": ["Master's degree in Law with at least 55% marks; Ph.D. preferred.", "Record of publications and teaching experience as per UGC norms."],
	"ss": ["Master's degree in a social science discipline with at least 55% marks; Ph.D. preferred.", "Teaching and research experience as per UGC norms."],
}


def justification_html(job):
	reasons = {
		"cfo": "The post of Chief Finance Officer has been held on additional charge since March 2026. A full-time CFO is essential for the FY 2026-27 audit and the move to accrual accounting.",
		"pnc": "With faculty and staff strength growing to over 400, the People and Culture team needs an Assistant Manager to handle recruitment and onboarding volume.",
		"assoc_law": "Two sanctioned Associate Professor (Law) posts are vacant following one superannuation and one resignation; the reservation roster point for the second post is SC.",
		"ra_will": "Two Research Associates are required under the NVF-funded WILL Initiative, as approved in the grant budget for 2026-28.",
		"ap_ss": "Three 2-year contract posts are needed to cover social science courses in the BA LLB (Hons.) programme from the coming trimester.",
		"pace": "PACE is expanding its distance education portfolio and needs a full-time Manager to run programme operations.",
		"ap_law": "Four 2-year contract Assistant Professors are needed to meet the student-teacher ratio for the incoming batch.",
		"gd": "Communications requires a Graphic Designer on consultancy to support publications, events and the website refresh.",
		"pd_will": "The WILL Initiative grant provides for a Project Director to lead implementation across partner states.",
		"assoc_hss": "Two Associate Professor posts in Humanities and Social Sciences are proposed under the faculty expansion plan.",
		"am_fin": "An Assistant Manager - Finance is required to strengthen payables, payroll and compliance as transaction volumes grow.",
	}
	return f"<p>{reasons.get(job.key, 'Post required for the functioning of the department.')}</p><p>The post will be filled through open advertisement, following the University's recruitment rules.</p>"


def shortlisting_note_html(job, received, shortlisted, final):
	return (
		f"<p>{received} applications were received for the post of {job.title}. The Shortlisting Committee shortlisted "
		f"{shortlisted} candidates, who were invited for an HR interaction. Based on the HR assessors' recommendations, "
		f"{final} candidates are placed on the final shortlist for the interview before the Selection Committee.</p>"
	)


def cv_lines(who, quals, employment):
	lines = [who.email, who.mobile, who.address.replace("\n", ", "), "", "EDUCATION"]
	for q in quals:
		lines.append(f"  {q['degree_name']}, {q['other_institution']} ({q['year_of_graduation']})")
	lines += ["", "EXPERIENCE"]
	for e in employment:
		lines.append(f"  {e['designation']}, {e['employer_name']} ({e['from_date'][:4]} - {'present' if e['is_current'] else e['to_date'][:4]})")
	if not employment:
		lines.append("  Fresh graduate")
	return lines


def sop_lines(who, job):
	return [
		f"I am applying for the post of {job.title} at NLSIU.",
		f"Over {who.seniority} years I have built experience that matches the responsibilities of this role,",
		"and I would value the opportunity to contribute to the University's work.",
		"",
		who.full_name,
	]


def reference_answer(row, who, rng):
	if row.answer_type == "Rating 1-5":
		return {"rating_value": 5 if who.strength > 0.8 else 4}
	if row.answer_type == "Yes-No":
		return {"answer_text": "Yes"}
	return {"answer_text": rng.choice(REFERENCE_TEXT).format(first=who.first)}


REFERENCE_TEXT = [
	"{first} reported to me directly for about three years and handled the work independently.",
	"Very dependable; {first} meets deadlines and keeps colleagues informed.",
	"{first} works well with teams and is respected by peers and juniors alike.",
	"Thorough and careful with detail; the quality of {first}'s work has been consistently high.",
	"{first} could delegate more, but this has improved with experience.",
	"I would certainly rehire {first} and recommend them for this position.",
]


def onboarding_file(document_type, who):
	slug = _slug(who.full_name)
	if document_type == "Digital Photograph":
		return f"{slug}-Photograph.png", photo_png(who.seq)
	if document_type.startswith("Profile Write-up"):
		return f"{slug}-Profile.docx", make_docx(
			[
				who.full_name,
				f"{who.first} brings {who.seniority} years of experience and joins NLSIU after roles in leading institutions. "
				f"{who.first} is interested in institution building and mentoring young professionals.",
			]
		)
	return f"{slug}-{_slug(document_type)}.pdf", make_pdf(document_type, [who.full_name, f"Submitted for onboarding - ref {frappe.generate_hash(length=8)}"])
