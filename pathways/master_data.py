# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Recruitment master records for NLSIU, taken from the recruitment
toolkit: the Google application forms (Law & SS drop-down lists,
specialisations, UGC NET subjects, screening questions, uploads), the
website notifications, the pre/post-interview green sheets, the
shortlisting and interview score sheets and the onboarding checklist.

seed_master_data() only adds what is missing. A record that already
exists — by name, or by its unique fields for the naming-series masters —
is left exactly as HR maintains it from Master Setup, so it is safe to
run on every install and migrate.
"""

import frappe

# ------------------------------------------------------------ organisation

TRACKS = [
	("Admin", "ADMIN", "Non-teaching administrative staff"),
	("Faculty", "FACULTY", "Teaching staff - Assistant and Associate Professors"),
	("Research", "RESEARCH", "Research and project staff, including grant-funded projects"),
]

# (department_name, department_code)
DEPARTMENTS = [
	("Finance", "FIN"),
	("People and Culture", "PNC"),
	("Communications", "COMMS"),
	("Professional and Continuing Education", "PACE"),
	("Academic Administration", "ACAD-ADMIN"),
	("Admissions and Outreach", "ADM-OUT"),
	("Centre for the Study of the Legal Profession", "CSLP"),
	("Law", "LAW"),
	("Humanities and Social Sciences", "HSS"),
]

# (designation_name, track, employment_type, pay_level_range, superannuation_age)
DESIGNATIONS = [
	("Assistant Manager - Finance", "Admin", "Permanent", "5/6/7/8", 60),
	("Assistant Manager - People and Culture", "Admin", "Permanent", "5/6/7", 60),
	("Manager - Academic Administration", "Admin", "Permanent", "8/9/10/11", 60),
	("Manager - Professional and Continuing Education", "Admin", "Permanent", None, None),
	("Chief Finance Officer", "Admin", "Permanent", None, None),
	("Graphic Designer", "Admin", "Consultant", "Rs. 50,000 - 70,000 per month", None),
	("Senior Consultant - Admissions and Outreach", "Admin", "Consultant", None, None),
	("Project Director", "Research", "Contract", None, None),
	("Senior Research Associate", "Research", "Consultant", None, None),
	("Research Associate", "Research", "Consultant", None, None),
	("Assistant Professor (Contract)", "Faculty", "Contract", "10 (consolidated, VII CPC)", None),
	("Associate Professor", "Faculty", "Permanent", "13A (VII CPC)", 65),
]

# ------------------------------------------------------------- documents

ANY_FORMAT = "PDF, JPG, JPEG, PNG"

# (document_name, used_in, requirement, track, max_file_size_mb, allowed_formats)
# Uploads that only some posts ask for are "If Applicable" here and made
# mandatory on the Position that needs them. Degree certificates and
# transcripts, CV, SOP and publications are part of the form itself.
DOCUMENT_TYPES = [
	# Application - every track (Identity Proof and Experience Certificates
	# #1/#2 come from pathways.install). Latest Pay Slip is on the onboarding
	# checklist too, so an existing Application-only record is widened.
	("Latest Pay Slip", "Both", "Mandatory", None, 2, ANY_FORMAT),
	("No-Objection Certificate", "Both", "If Applicable", None, 1, ANY_FORMAT),
	# Application - Faculty
	("NET / SLET / SET Certificate", "Application", "If Applicable", "Faculty", 1, ANY_FORMAT),
	("Caste Certificate", "Application", "If Applicable", "Faculty", 1, ANY_FORMAT),
	("Certificate of Disability", "Application", "If Applicable", "Faculty", 1, ANY_FORMAT),
	("Experience Certificate #3", "Application", "If Applicable", "Faculty", 1, ANY_FORMAT),
	("Experience Certificate #4", "Application", "If Applicable", "Faculty", 1, ANY_FORMAT),
	("Scanned Copies of Books / Journals / Book Chapters", "Application", "If Applicable", "Faculty", 10, "PDF"),
	("Self-declared API Score Sheet", "Application", "If Applicable", "Faculty", 1, "PDF, DOC, DOCX"),
	("Teaching / Research Experience Statement", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Publications", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Administrative / Institutional Posts Held", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Papers Published in Conference Proceedings", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Papers Presented in Conferences (Unpublished)", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Sponsored Research Projects", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Research Projects", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Consultancies", "Application", "If Applicable", "Faculty", 1, "PDF"),
	("List of Research Guidance (PhD / Masters Dissertations)", "Application", "If Applicable", "Faculty", 1, "PDF"),
	# Application - Research
	("Writing Sample", "Application", "If Applicable", "Research", 2, "PDF"),
	("Research Publication / Equivalent Output", "Application", "If Applicable", "Research", 2, "PDF"),
	# Application - Admin
	("Design Portfolio / Sample Work", "Application", "If Applicable", "Admin", 5, "PDF"),
	# Onboarding - documents to bring on the day of joining
	("PAN", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Aadhaar", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Digital Photograph", "Onboarding", "Mandatory", None, 2, "JPG, JPEG, PNG"),
	("Passport", "Onboarding", "Optional", None, 2, ANY_FORMAT),
	("Signed Appointment Order", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Class X Certificate", "Onboarding", "Mandatory", None, 1, ANY_FORMAT),
	("Class XII Certificate", "Onboarding", "Mandatory", None, 1, ANY_FORMAT),
	("Graduation I Certificate", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Graduation Transcripts", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Graduation II Certificate", "Onboarding", "If Applicable", None, 2, ANY_FORMAT),
	("Post Graduation I Certificate", "Onboarding", "If Applicable", None, 2, ANY_FORMAT),
	("Post Graduation Transcripts", "Onboarding", "If Applicable", None, 2, ANY_FORMAT),
	("Post Graduation II Certificate", "Onboarding", "If Applicable", None, 2, ANY_FORMAT),
	("Relieving Letter", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Provident Fund UAN", "Onboarding", "If Applicable", None, 2, ANY_FORMAT),
	("Updated CV", "Onboarding", "Mandatory", None, 2, "PDF"),
	("PAN-Aadhaar Link Proof", "Onboarding", "Mandatory", None, 2, ANY_FORMAT),
	("Profile Write-up (max 200 words)", "Onboarding", "Mandatory", None, 1, "DOC, DOCX"),
]

# ----------------------------------------------------------- qualifications

# Specialisations in the order the application forms list them ("Other" is
# added by the form itself).
SPECIALIZATIONS = {
	"Law": [
		"Contracts Law",
		"Property Law",
		"Criminal Law",
		"Torts",
		"Constitutional Law",
		"Administrative Law",
		"Intellectual Property Rights",
		"Company Law",
		"Labour Law",
		"Public International Law",
		"Human Rights",
		"Family Law",
		"Jurisprudence",
		"Civil Procedure",
		"Environmental Law",
		"Taxation Law",
		"Alternative Dispute Resolution",
		"Conflict of Laws",
		"Financial Sector Regulation",
		"International Trade Law",
		"Professional Ethics",
		"Drafting",
		"Law of Evidence",
	],
	"Social Science": [
		"Economics",
		"Sociology",
		"Political Science",
		"History",
	],
}

# UGC NET subjects as on the faculty application forms. Four official
# names are longer than a record name may be (140 characters) and are
# abbreviated: Economics/..., Management (...), Politics incl. ...,
# Sanskrit traditional subjects (...).
UGC_NET_SUBJECTS = [
	"Adult Education/Continuing Education/Andragogy/Non-Formal Education",
	"Anthropology",
	"Arab Culture and Islamic Studies",
	"Arabic",
	"Archaeology",
	"Assamese",
	"Bengali",
	"Bodo",
	"Buddhist, Jaina, Gandhian, and Peace Studies",
	"Chinese",
	"Commerce",
	"Comparative Literature",
	"Comparative Study of Religions",
	"Computer Science and Applications",
	"Criminology",
	"Defence and Strategic Studies",
	"Dogri",
	"Economics/Rural Eco./Co-operation/Demography/Development Planning/Development Studies/Econometrics/Applied/Development/Business Economics",
	"Education",
	"Electronic Science",
	"English",
	"Environmental Sciences",
	"Folk Literature",
	"Forensic Science",
	"French (French Version)",
	"Geography",
	"German",
	"Gujarati",
	"Hindi",
	"Hindu Studies",
	"History",
	"Home Science",
	"Human Rights and Duties",
	"Indian Culture",
	"Japanese",
	"Kannada",
	"Kashmiri",
	"Konkani",
	"Labour Welfare/Personnel Management/Industrial Relations/Labour and Social Welfare/Human Resource Management",
	"Law",
	"Library and Information Science",
	"Linguistics",
	"Maithili",
	"Malayalam",
	"Management (incl. Business Admn./Marketing/Marketing Mgt./IR & Personnel Mgt./Personnel Mgt./Financial Mgt./Co-operative Mgt.)",
	"Manipuri",
	"Marathi",
	"Mass Communication and Journalism",
	"Museology & Conservation",
	"Music",
	"Nepali",
	"Oriya",
	"Pali",
	"Performing Art - Dance/Drama/Theatre",
	"Persian",
	"Philosophy",
	"Physical Education",
	"Political Science",
	"Politics incl. International Relations/Studies, Defence/Strategic, West Asian, SE Asian, African, South Asian, Soviet, American Studies",
	"Population Studies",
	"Prakrit",
	"Psychology",
	"Public Administration",
	"Punjabi",
	"Rajasthani",
	"Russian",
	"Sanskrit",
	"Sanskrit traditional subjects (incl. Jyotisha/Vyakarna/Mimansa/Navya Nyaya/Sankhya Yoga/Tulanatmaka Darsan/Vedant/Dharmasasta/Agama etc.)",
	"Santali",
	"Sindhi",
	"Social Medicine & Community Health",
	"Social Work",
	"Sociology",
	"Spanish",
	"Tamil",
	"Telugu",
	"Tourism Administration and Management",
	"Tribal and Regional Language/Literature",
	"Urdu",
	"Visual Art (including Drawing & Painting/Sculpture Graphics/Applied Art/History of Art)",
	"Women Studies",
	"Yoga",
	"Indian Knowledge System",
	"Disaster Management",
	"Ayurveda Biology",
]

# Institution drop-down lists of the Law and Social Science faculty forms
# (Law & SS Drop Down List.xlsx), spelt as on the forms.
INSTITUTIONS_LAW = [
	"Aligarh Muslim University",
	"Alliance University",
	"Amity University Haryana, Gurgaon",
	"Army Institute of Law",
	"Babasheb Bhimrao Ambedkar University",
	"BML Munjal University (BMU)",
	"Central University of Punjab",
	"Central University of South Bihar",
	"Chanakya National Law University(CNLU), Patna",
	"Christ University",
	"Cochin University of Science and Technology",
	"Damodaramsanjivayya National Law University (DSNLU), Visakhapatnam",
	"Dharmashastra national law university, Jabalpur (M.P)",
	"Dr. B. R. Ambedkar College of Law",
	"Dr. B.R. Ambedkar National Law University",
	"Dr. Rajendra Prasad National Law University, Prayagraj",
	"Dr. Ram Manohar Lohiya National Law University (RMLNLU), Lucknow",
	"Faculty of Law, University of Delhi",
	"Galgotias University",
	"Gandhi Institute of Technology And Management (GITAM)",
	"Gujarat National Law University(GNLU), Gandhinagar",
	"Guru Gobind Singh Indraprastha University",
	"Hidayatullah National Law University (HNLU), Raipur",
	"Himachal Pradesh National Law University,Shimla",
	"ICFAI Foundation for Higher Education,Hyderabad",
	"India International University of Legal Education and Research, India (IIULER), Goa",
	"Indian Institute of Technology Kharagpur",
	"Jadavpur University",
	"Jamia Millia Islamia",
	"Kalinga Institute of Industrial Technology",
	"Lovely Professional University",
	"Maharashtra National Law University (MNLU), Aurangabad",
	"Maharashtra National Law University (MNLU), Mumbai",
	"Maharashtra National Law University,Nagpur",
	"Manipal Academy of Higher Education",
	"Manipal Law school",
	"Manipal University Jaipur",
	"NALSAR University of Law (NALSAR), Hyderabad",
	"National Law Institute University,Bhopal",
	"National Law School India Univerity",
	"National Law University and Judicial Academy (NLUJA), Assam",
	"National Law University Odisha (NLUO), Cuttack",
	"National Law University, Delhi",
	"National Law University, Tripura",
	"National University of Advanced Legal Studies (NUALS), Kochi",
	"National University of Study and Research in Law(NUSRL), Ranchi",
	"Nirma University",
	"O.P. Jindal Global University (JGU)",
	"OP Jindal Global Law School (JGLS)",
	"Panjab University",
	"Rajiv Gandhi National University of Law (RGNUL), Punjab",
	"S.R.M. Institute of Science and Technology",
	"Saveetha Institute of Medical and Technical Sciences",
	"Savitribai Phule Pune University",
	"Shanmugha Arts Science Technology & Research Academy",
	"Shiv Nadar University (SNU)",
	"Siksha `O`Anusandhan",
	"Symbiosis Law School, Pune",
	"Tamil Nadu National Law University (TNNLU), Tiruchirappalli",
	"The National Law institute University (NLIU)",
	"The National Law University (NLU), Jodhpur",
	"The West Bengal National University of Juridical Sciences (WBNUJS), Kolkata",
	"University of Calcutta",
	"University of Kashmir",
	"University of Lucknow",
	"University of Mumbai",
	"UPES",
]

INSTITUTIONS_SOCIAL_SCIENCE = [
	"Acharya Nagarjuna University",
	"Alagappa University",
	"Aligarh Muslim University",
	"Amity University",
	"Amrita Vishwa Vidyapeetham",
	"Andhra University, Visakhapatnam",
	"Anna University",
	"Assam University-Silchar",
	"Avinashilingam Institute for Home Science & Higher Education for Women",
	"Babasheb Bhimrao Ambedkar University",
	"Banaras Hindu University",
	"Banasthali Vidyapith",
	"Bangalore University",
	"Bharath Institute of Higher Education & Research",
	"Bharathiar University",
	"Bharathidasan University",
	"Bharati Vidyapeeth",
	"Birla Institute of Technology",
	"Birla Institute of Technology & Science -Pilani",
	"Calcutta University",
	"Central University of Punjab",
	"Central University of Rajasthan",
	"Central University of Tamil Nadu",
	"Chandigarh University",
	"Chettinad Academy of Research and Education",
	"Chitkara University",
	"Christ University",
	"Cochin University of Science and Technology",
	"Datta Meghe Institute of Higher Education and Research",
	"Delhi Technological University",
	"Dr. D. Y. Patil Vidyapeeth",
	"Gandhi Institute of Technology And Management (GITAM)",
	"Gauhati University",
	"Graphic Era University",
	"Gujarat University",
	"Guru Gobind Singh Indraprastha University",
	"Homi Bhabha National Institute",
	"Indian Agricultural Research Institute",
	"Indian Institute of Science",
	"Indraprastha Institute of Information Technology",
	"Institute of Chemical Technology",
	"International Institute of Information Technology Hyderabad",
	"Jadavpur University",
	"Jain university,Bangalore",
	"Jamia Hamdard",
	"Jamia Millia Islamia",
	"Jawaharlal Nehru Technological University",
	"Jawaharlal Nehru University",
	"JSS Academy of Higher Education and Research",
	"Kalasalingam Academy of Research and Education",
	"Kalinga Institute of Industrial Technology",
	"Kerala University",
	"King George`s Medical University",
	"Koneru Lakshmaiah Education Foundation University (K L College of Engineering)",
	"Lovely Professional University",
	"Madan Mohan Malaviya University of Technology",
	"Madurai Kamaraj University",
	"Maharishi Markandeshwar",
	"Mahatma Gandhi University, Kottayam",
	"Manav Rachna International Institute of Research & Studies",
	"Manipal Academy of Higher Education-Manipal",
	"Manipal University Jaipur",
	"Mizoram University",
	"Mumbai University",
	"Mysore University",
	"NITTE",
	"Osmania University",
	"Padmashree Dr. D. Y. Patil Vidyapeeth, Mumbai",
	"Panjab University",
	"Periyar University",
	"Punjab Agricultural University",
	"S.R.M. Institute of Science and Technology",
	"Sant Longowal Institute of Engineering & Technology",
	"Sathyabama Institute of Science and Technology",
	"Saveetha Institute of Medical and Technical Sciences",
	"Savitribai Phule Pune University",
	"Shanmugha Arts Science Technology & Research Academy",
	"Sharda University",
	"Sher-e-Kashmir University of Agricultural Science and Technology of Kashmir",
	"Shiv Nadar University",
	"Shoolini University of Biotechnology and Management Sciences",
	"Siksha `O` Anusandhan",
	"Sri Balaji Vidyapeeth Mahatma Gandhi Medical College Campus",
	"Sri Ramachandra Institute of Higher Education and Research",
	"SVKM`s Narsee Monjee Institute of Management Studies",
	"Symbiosis International",
	"Tamil Nadu Agricultural University",
	"Tata Institute of Social Sciences",
	"Tezpur University",
	"Thapar Institute of Engineering and Technology (Deemed-to-be-university)",
	"University of Agricultural Sciences, Bangalore",
	"University of Delhi",
	"University of Hyderabad",
	"University of Jammu",
	"University of Kashmir",
	"University of Lucknow",
	"University of Madras",
	"UPES",
	"Vellore Institute of Technology",
	"Vignan's Foundation for Science, Technology and Research",
]

# --------------------------------------------------------------- positions


def _yes_no(question, mandatory=1, details=0):
	return {"question": question, "answer_type": "Yes/No", "is_mandatory": mandatory, "ask_details_if_yes": details}


MASTERS_55 = _yes_no(
	"Do you have a Master's Degree with at least 55% marks (or an equivalent grade in a point-scale, "
	"wherever the grading system is followed)?"
)

FACULTY_FORM = {
	"require_postgraduate": 1,
	"ask_specialization": 1,
	"ask_category_disability": 1,
	"ask_phd": 1,
	"ask_net": 1,
	"ask_experience_months": 1,
	"ask_admin_responsibilities": 1,
	"ask_publications": 1,
}

IDENTITY_PROOF = "Identity Proof (Aadhaar / PAN / Passport / DL / Voter ID)"

# (document_type, is_mandatory)
ASSISTANT_PROFESSOR_DOCUMENTS = [
	(IDENTITY_PROOF, 1),
	("Class X Certificate", 1),
	("Class XII Certificate", 1),
	("NET / SLET / SET Certificate", 0),
	("Experience Certificate #1", 0),
	("Experience Certificate #2", 0),
	("No-Objection Certificate", 0),
	("Caste Certificate", 0),
	("Certificate of Disability", 0),
	("Latest Pay Slip", 0),
	("Scanned Copies of Books / Journals / Book Chapters", 0),
]

ASSOCIATE_PROFESSOR_DOCUMENTS = [
	(IDENTITY_PROOF, 1),
	("Class X Certificate", 1),
	("Class XII Certificate", 1),
	("Self-declared API Score Sheet", 1),
	("Teaching / Research Experience Statement", 1),
	("List of Publications", 1),
	("Scanned Copies of Books / Journals / Book Chapters", 1),
	("NET / SLET / SET Certificate", 0),
	("Experience Certificate #1", 1),
	("Experience Certificate #2", 0),
	("Experience Certificate #3", 0),
	("Experience Certificate #4", 0),
	("No-Objection Certificate", 0),
	("Caste Certificate", 0),
	("Certificate of Disability", 0),
	("Latest Pay Slip", 1),
	("List of Administrative / Institutional Posts Held", 1),
	("List of Papers Published in Conference Proceedings", 1),
	("List of Papers Presented in Conferences (Unpublished)", 1),
	("List of Sponsored Research Projects", 1),
	("List of Research Projects", 1),
	("List of Consultancies", 1),
	("List of Research Guidance (PhD / Masters Dissertations)", 1),
]

ASSOCIATE_PROFESSOR_QUESTIONS = [
	MASTERS_55,
	_yes_no("Do you have a total research score of 75 as per the UGC Regulations, 2018?"),
	_yes_no(
		"Do you have a minimum of 8 years of teaching experience in university/college as an "
		"Assistant Professor and/or research experience?"
	),
	_yes_no("Do you have a minimum of 7 research publications in peer-reviewed or UGC-listed journals?"),
]

STANDARD_STAFF_DOCUMENTS = [
	(IDENTITY_PROOF, 1),
	("Experience Certificate #1", 1),
	("Experience Certificate #2", 0),
	("Latest Pay Slip", 1),
]

PERMANENT_60 = (
	"Permanent basis till the age of superannuation i.e. 60 years, subject to confirmation after the "
	"satisfactory completion of two years' probation."
)

# Positions not listed with required_documents use the Document Type
# Master defaults for their track.
POSITIONS = [
	# Admin
	{
		"job_code": "ADM-AM-FIN",
		"position_title": "Assistant Manager - Finance",
		"track": "Admin",
		"department": "Finance",
		"designation": "Assistant Manager - Finance",
	},
	{
		"job_code": "ADM-AM-PNC",
		"position_title": "Assistant Manager - People and Culture",
		"track": "Admin",
		"department": "People and Culture",
		"designation": "Assistant Manager - People and Culture",
		"tenure_description": PERMANENT_60,
		"require_postgraduate": 1,
		"screening_questions": [
			_yes_no("Do you have 4+ years of relevant work experience in a People and Culture function?"),
			_yes_no("Do you have a strong understanding of academic recruitment processes?", details=1),
			_yes_no("Do you have proficiency in HRMS, ERP and/or Google Suite?", details=1),
		],
		"required_documents": [*STANDARD_STAFF_DOCUMENTS, ("No-Objection Certificate", 0)],
	},
	{
		"job_code": "ADM-MGR-ACAD",
		"position_title": "Manager - Academic Administration",
		"track": "Admin",
		"department": "Academic Administration",
		"designation": "Manager - Academic Administration",
		"tenure_description": "On pay scale, full time, till superannuation.",
	},
	{
		"job_code": "ADM-MGR-PACE",
		"position_title": "Manager - Professional and Continuing Education (PACE)",
		"track": "Admin",
		"department": "Professional and Continuing Education",
		"designation": "Manager - Professional and Continuing Education",
		"screening_questions": [
			_yes_no("Do you have 7-10 years of experience in complex operation process roles?", details=1),
			_yes_no(
				"Do you have prior experience in managing end-to-end distance education programmes?",
				mandatory=0,
				details=1,
			),
			_yes_no(
				"Do you have prior experience in academic administration or academic operations roles?",
				mandatory=0,
				details=1,
			),
		],
		"required_documents": STANDARD_STAFF_DOCUMENTS,
	},
	{
		"job_code": "ADM-CFO",
		"position_title": "Chief Finance Officer",
		"track": "Admin",
		"department": "Finance",
		"designation": "Chief Finance Officer",
		"require_postgraduate": 1,
		"screening_questions": [
			{
				"question": "Please indicate your professional qualification.",
				"answer_type": "Single Choice",
				"options": "Chartered Accountant (CA)\nCost and Management Accountant (CMA)\nBoth CA and CMA\nPursuing CA\nPursuing CMA",
				"is_mandatory": 0,
			},
			_yes_no(
				"Do you have a minimum of 15 years of administrative experience in a supervisory position, "
				"maintaining audited accounts, preparing budgets, managing procurement, and ensuring compliance?",
				details=1,
			),
		],
		"required_documents": STANDARD_STAFF_DOCUMENTS,
	},
	{
		"job_code": "ADM-GD",
		"position_title": "Graphic Designer",
		"track": "Admin",
		"department": "Communications",
		"designation": "Graphic Designer",
		"tenure_description": "Full-time, campus-based contractual role for one year (extendable).",
		"required_documents": [
			(IDENTITY_PROOF, 1),
			("Writing Sample", 1),
			("Design Portfolio / Sample Work", 1),
			("Experience Certificate #1", 0),
			("Experience Certificate #2", 0),
			("Latest Pay Slip", 0),
		],
	},
	{
		"job_code": "ADM-SC-AO",
		"position_title": "Senior Consultant - Admissions and Outreach",
		"track": "Admin",
		"department": "Admissions and Outreach",
		"designation": "Senior Consultant - Admissions and Outreach",
		"tenure_description": "Based out of the University campus for a period of one year (extendable).",
	},
	# Research
	{
		"job_code": "RES-PD-WILL",
		"position_title": "Project Director - Women's Inclusion and Leadership in Law (WILL) Initiative",
		"track": "Research",
		"department": "Centre for the Study of the Legal Profession",
		"designation": "Project Director",
		"tenure_description": (
			"Full-time, contractual, at the NLSIU campus in Bengaluru. Initially for two years, extendable "
			"for the project duration subject to performance."
		),
		"screening_questions": [
			_yes_no("Do you have at least 10 years of post-qualification experience?"),
			_yes_no("Do you have a demonstrated track record in project management and team leadership?", details=1),
			_yes_no("Do you have experience leading large scale multi-state project implementation?", mandatory=0, details=1),
			_yes_no("Do you have prior experience in litigation/law firm practice?", mandatory=0, details=1),
		],
		"required_documents": STANDARD_STAFF_DOCUMENTS,
	},
	{
		"job_code": "RES-RA-WILL",
		"position_title": "Research Associate - Women's Inclusion and Leadership in Law (WILL) Initiative",
		"track": "Research",
		"department": "Centre for the Study of the Legal Profession",
		"designation": "Research Associate",
		"tenure_description": (
			"Full-time, based out of the NLSIU campus in Bengaluru. One year from the date of joining, "
			"extendable for the project duration subject to satisfactory performance."
		),
		"screening_questions": [
			_yes_no(
				"Do you have at least 2 years of relevant post-qualification work experience in legal research, "
				"policy engagement and/or action-based research projects?"
			),
		],
		"required_documents": [
			(IDENTITY_PROOF, 1),
			("Writing Sample", 1),
			("Research Publication / Equivalent Output", 0),
			("Experience Certificate #1", 0),
			("Experience Certificate #2", 0),
			("Latest Pay Slip", 0),
		],
	},
	# Faculty
	{
		"job_code": "FAC-AP-LAW-2Y",
		"position_title": "Assistant Professor (Law) - 2-Year Contract",
		"track": "Faculty",
		"department": "Law",
		"designation": "Assistant Professor (Contract)",
		"tenure_description": "Contractual appointment for a maximum period of 24 months.",
		**FACULTY_FORM,
		"institution_list": "Law",
		"specialization_discipline": "Law",
		"min_publications": 1,
		"max_publications": 3,
		"screening_questions": [MASTERS_55],
		"required_documents": ASSISTANT_PROFESSOR_DOCUMENTS,
	},
	{
		"job_code": "FAC-AP-SS-2Y",
		"position_title": "Assistant Professor (Social Science) - 2-Year Contract",
		"track": "Faculty",
		"department": "Humanities and Social Sciences",
		"designation": "Assistant Professor (Contract)",
		"tenure_description": "Contractual appointment for a maximum period of 24 months.",
		**FACULTY_FORM,
		"institution_list": "Social Science",
		"specialization_discipline": "Social Science",
		"min_publications": 1,
		"max_publications": 3,
		"screening_questions": [MASTERS_55],
		"required_documents": ASSISTANT_PROFESSOR_DOCUMENTS,
	},
	{
		"job_code": "FAC-ASSOC-LAW",
		"position_title": "Associate Professor (Law)",
		"track": "Faculty",
		"department": "Law",
		"designation": "Associate Professor",
		"tenure_description": (
			"Permanent basis till the age of superannuation i.e. 65 years, subject to confirmation after the "
			"satisfactory completion of two years' probation."
		),
		**FACULTY_FORM,
		"institution_list": "Law",
		"specialization_discipline": "Law",
		"min_publications": 3,
		"max_publications": 3,
		"screening_questions": ASSOCIATE_PROFESSOR_QUESTIONS,
		"required_documents": ASSOCIATE_PROFESSOR_DOCUMENTS,
	},
	{
		"job_code": "FAC-ASSOC-HSS",
		"position_title": "Associate Professor (Humanities and Social Science)",
		"track": "Faculty",
		"department": "Humanities and Social Sciences",
		"designation": "Associate Professor",
		"tenure_description": (
			"Permanent basis till the age of superannuation i.e. 65 years, subject to confirmation after the "
			"satisfactory completion of two years' probation."
		),
		**FACULTY_FORM,
		"institution_list": "Social Science",
		"specialization_discipline": "Social Science",
		"min_publications": 3,
		"max_publications": 3,
		"screening_questions": ASSOCIATE_PROFESSOR_QUESTIONS,
		"required_documents": ASSOCIATE_PROFESSOR_DOCUMENTS,
	},
]

# --------------------------------------------------------- approval chains

# Signatories as on the green sheets, in signing order: (role, label).
# Project-specific signatories (e.g. the Director of a grant-funded
# initiative) are added per project as a User step.
ADMIN_POST_INTERVIEW_STEPS = [
	("Pathways Recruiter", "Recruiter"),
	("Pathways Director People Culture", "Director - People and Culture"),
	("Pathways CFO", "Chief Finance Officer"),
	("Pathways Registrar", "Registrar"),
	("Pathways Vice Chancellor", "Vice Chancellor"),
]

APPROVAL_CHAINS = [
	{
		"template_name": "Admin - Pre-Recruitment Green Sheet",
		"track": "Admin",
		"applies_to": "Pre-Recruitment Green Sheet",
		"steps": [
			("Pathways Recruiter", "Executive - People and Culture"),
			("Pathways PNCO", "PNCO"),
			("Pathways Registrar", "Registrar"),
			("Pathways Vice Chancellor", "Vice Chancellor"),
		],
	},
	{
		"template_name": "Admin - Post-Interview Green Sheet",
		"track": "Admin",
		"applies_to": "Post-Interview Green Sheet",
		"steps": ADMIN_POST_INTERVIEW_STEPS,
	},
	{
		"template_name": "Faculty - Pre-Recruitment Green Sheet",
		"track": "Faculty",
		"applies_to": "Pre-Recruitment Green Sheet",
		"steps": [
			("Pathways Recruiter", "Recruiter"),
			("Pathways PNCO", "PNCO"),
			("Pathways Dean Academics", "Dean Academics"),
			("Pathways Registrar", "Registrar"),
			("Pathways Vice Chancellor", "Vice Chancellor"),
		],
	},
	{
		"template_name": "Research - Pre-Recruitment Green Sheet",
		"track": "Research",
		"applies_to": "Pre-Recruitment Green Sheet",
		"steps": [
			("Pathways Senior Manager Research", "Senior Manager Research"),
			("Pathways Director People Culture", "Director - People and Culture"),
			("Pathways Dean Research", "Dean Research"),
			("Pathways Registrar", "Registrar"),
			("Pathways Vice Chancellor", "Vice Chancellor"),
		],
	},
	{
		"template_name": "Research - Post-Interview Green Sheet",
		"track": "Research",
		"applies_to": "Post-Interview Green Sheet",
		"steps": [
			("Pathways Recruiter", "Assistant Manager - People and Culture"),
			("Pathways Senior Manager Research", "Senior Manager Research"),
			("Pathways CFO", "Chief Finance Officer"),
			("Pathways Dean Research", "Dean Research"),
			("Pathways Director People Culture", "Director - People and Culture"),
			("Pathways Registrar", "Registrar"),
			("Pathways Vice Chancellor", "Vice Chancellor"),
		],
	},
]

# ---------------------------------------------------------- scoring rubrics

DOMAIN_KNOWLEDGE = "Does the candidate demonstrate knowledge of their {0}? Does the candidate organise their ideas and arguments well?"
RESPONSES = "Does the candidate listen carefully and understand questions posed? Does the candidate respond adequately to the questions posed?"
SUITABILITY_STAFF = "Is the candidate likely to contribute to NLSIU? Is the candidate's attitude suitable for the role and for NLSIU?"
SUITABILITY_FACULTY = (
	"Is the candidate likely to contribute to NLSIU? Is the candidate likely to excel and become a leader "
	"in their academic field?"
)

# (criterion_label, max_score, guidance_text). A candidate needs 50% of the
# total interview score to be eligible for an offer.
SCORING_RUBRICS = [
	{
		"rubric_name": "Admin - Shortlisting",
		"track": "Admin",
		"stage": "Shortlisting",
		"scoring_mode": "Pass/Fail Only",
		"criteria": [],
	},
	{
		"rubric_name": "Admin - Final Interview",
		"track": "Admin",
		"stage": "Final Interview",
		"scoring_mode": "Weighted Score",
		"criteria": [
			("Domain Knowledge", 20, DOMAIN_KNOWLEDGE.format("domain/field")),
			("Responses", 20, RESPONSES),
			("Overall Suitability", 10, SUITABILITY_STAFF),
		],
	},
	{
		"rubric_name": "Faculty - Shortlisting",
		"track": "Faculty",
		"stage": "Shortlisting",
		"scoring_mode": "Weighted Score",
		"criteria": [
			("Education (excluding PhD)", 50, None),
			("Publications", 10, None),
			("Teaching Experience", 5, None),
			("Administrative Experience", 5, None),
		],
	},
	{
		"rubric_name": "Faculty - Final Interview",
		"track": "Faculty",
		"stage": "Final Interview",
		"scoring_mode": "Weighted Score",
		"criteria": [
			("Domain Knowledge", 40, DOMAIN_KNOWLEDGE.format("academic field")),
			("Responses", 30, RESPONSES),
			("Overall Suitability", 30, SUITABILITY_FACULTY),
		],
	},
	{
		"rubric_name": "Research - Shortlisting",
		"track": "Research",
		"stage": "Shortlisting",
		"scoring_mode": "Weighted Score",
		"criteria": [
			("Education", 4, "Reference: CV"),
			("Overall Experience and SOP", 4, "Reference: experience, SOP, writing sample and research publication"),
			("Overall", 4, "Reference: CV"),
		],
	},
	{
		"rubric_name": "Research - Final Interview",
		"track": "Research",
		"stage": "Final Interview",
		"scoring_mode": "Weighted Score",
		"criteria": [
			("Domain Knowledge", 20, DOMAIN_KNOWLEDGE.format("domain/field")),
			("Responses", 20, RESPONSES),
			("Overall Suitability", 10, SUITABILITY_STAFF),
		],
	},
]


# ------------------------------------------------------------------ seeding


def seed_master_data():
	"""Create the missing master records, parents before the records that
	link to them."""
	seed_tracks()
	seed_departments()
	seed_designations()
	seed_document_types()
	seed_specializations()
	seed_ugc_net_subjects()
	seed_institutions()
	seed_positions()
	seed_approval_chains()
	seed_scoring_rubrics()


def _insert(doc):
	frappe.get_doc(doc).insert(ignore_permissions=True)


def seed_tracks():
	for name, code, description in TRACKS:
		if frappe.db.exists("Recruitment Track", name) or frappe.db.exists("Recruitment Track", {"track_code": code}):
			continue
		_insert(
			{
				"doctype": "Recruitment Track",
				"track_name": name,
				"track_code": code,
				"description": description,
				"is_active": 1,
			}
		)


def seed_departments():
	for name, code in DEPARTMENTS:
		if frappe.db.exists("Department", name):
			continue
		# The code is unique but optional — never let it block the department.
		if frappe.db.exists("Department", {"department_code": code}):
			code = None
		_insert({"doctype": "Department", "department_name": name, "department_code": code, "is_active": 1})


def seed_designations():
	for name, track, employment_type, pay_level, superannuation_age in DESIGNATIONS:
		if frappe.db.exists("Designation", name):
			# A designation already on the site (made by hand or by another
			# app) gets the recruitment details it is missing; values that
			# are already set are left alone.
			current = frappe.db.get_value(
				"Designation", name, ["track", "employment_type", "pay_level_range", "superannuation_age"], as_dict=True
			) or {}
			missing = {
				field: value
				for field, value in (
					("track", track), ("employment_type", employment_type),
					("pay_level_range", pay_level), ("superannuation_age", superannuation_age),
				)
				if not current.get(field) and value
			}
			if missing:
				frappe.db.set_value("Designation", name, missing, update_modified=False)
			continue
		_insert(
			{
				"doctype": "Designation",
				"designation_name": name,
				"track": track,
				"employment_type": employment_type,
				"pay_level_range": pay_level,
				"superannuation_age": superannuation_age,
				"is_active": 1,
			}
		)


def seed_document_types():
	for name, used_in, requirement, track, max_size, formats in DOCUMENT_TYPES:
		existing = frappe.db.get_value("Document Type Master", name, "used_in")
		if existing:
			# Only ever widen to "Both", so a document HR uses at one stage is
			# also offered at the other; nothing else is touched.
			if used_in == "Both" and existing != "Both":
				frappe.db.set_value("Document Type Master", name, "used_in", "Both")
			continue
		_insert(
			{
				"doctype": "Document Type Master",
				"document_name": name,
				"used_in": used_in,
				"requirement": requirement,
				"track": track,
				"max_file_size_mb": max_size,
				"allowed_formats": formats,
				"is_active": 1,
			}
		)


def seed_specializations():
	for discipline, names in SPECIALIZATIONS.items():
		for name in names:
			if frappe.db.exists("Specialization Master", {"specialization_name": name, "discipline": discipline}):
				continue
			_insert(
				{
					"doctype": "Specialization Master",
					"specialization_name": name,
					"discipline": discipline,
					"is_active": 1,
				}
			)


def seed_ugc_net_subjects():
	for name in UGC_NET_SUBJECTS:
		if not frappe.db.exists("UGC NET Subject Master", name):
			_insert({"doctype": "UGC NET Subject Master", "subject_name": name, "is_active": 1})


def seed_institutions():
	"""An institution on both drop-down lists is one record of type Both."""
	law, social_science = set(INSTITUTIONS_LAW), set(INSTITUTIONS_SOCIAL_SCIENCE)
	for name in [*INSTITUTIONS_LAW, *(n for n in INSTITUTIONS_SOCIAL_SCIENCE if n not in law)]:
		if frappe.db.exists("Institution Master", {"institution_name": name}):
			continue
		list_type = "Both" if name in law and name in social_science else ("Law" if name in law else "Social Science")
		_insert({"doctype": "Institution Master", "institution_name": name, "list_type": list_type, "is_active": 1})


def seed_positions():
	for position in POSITIONS:
		if frappe.db.exists("Position", position["job_code"]):
			continue
		designation = frappe.db.get_value(
			"Designation", position["designation"], ["employment_type", "pay_level_range"], as_dict=True
		) or frappe._dict()
		# Fall back to the seeded defaults when the site's designation lacks them.
		default = next((d for d in DESIGNATIONS if d[0] == position["designation"]), None)
		doc = frappe.get_doc(
			{
				"doctype": "Position",
				"is_active": 1,
				"employment_type": designation.employment_type or (default[2] if default else None),
				"pay_level": designation.pay_level_range or (default[3] if default else None),
				**{k: v for k, v in position.items() if k not in ("screening_questions", "required_documents")},
			}
		)
		for question in position.get("screening_questions") or []:
			doc.append("screening_questions", dict(question))
		for document_type, is_mandatory in position.get("required_documents") or []:
			doc.append("required_documents", {"document_type": document_type, "is_mandatory": is_mandatory})
		doc.insert(ignore_permissions=True)


def _has_active_track_chain(track, applies_to):
	"""Only one active track-wide chain may answer a track + document type."""
	return any(
		not t.employment_type
		for t in frappe.get_all(
			"Approval Chain Template",
			filters={"track": track, "applies_to": applies_to, "is_active": 1},
			fields=["employment_type"],
		)
	)


def seed_approval_chains():
	for chain in APPROVAL_CHAINS:
		if frappe.db.exists("Approval Chain Template", chain["template_name"]):
			continue
		if _has_active_track_chain(chain["track"], chain["applies_to"]):
			continue
		_insert(
			{
				"doctype": "Approval Chain Template",
				"template_name": chain["template_name"],
				"track": chain["track"],
				"applies_to": chain["applies_to"],
				"is_active": 1,
				"steps": chain_steps(chain["steps"]),
			}
		)


def chain_steps(steps):
	return [
		{"sequence": sequence, "approver_type": "Role", "approver_role": role, "approver_label": label}
		for sequence, (role, label) in enumerate(steps, start=1)
	]


def seed_scoring_rubrics():
	for rubric in SCORING_RUBRICS:
		if frappe.db.exists("Scoring Rubric Template", rubric["rubric_name"]):
			continue
		# The scoring screens use the one active rubric per track + stage.
		if frappe.db.exists(
			"Scoring Rubric Template", {"track": rubric["track"], "stage": rubric["stage"], "is_active": 1}
		):
			continue
		_insert(
			{
				"doctype": "Scoring Rubric Template",
				"rubric_name": rubric["rubric_name"],
				"track": rubric["track"],
				"stage": rubric["stage"],
				"scoring_mode": rubric["scoring_mode"],
				"pass_threshold_percent": 50,
				"is_active": 1,
				"criteria": [
					{"criterion_label": label, "max_score": max_score, "guidance_text": guidance}
					for label, max_score, guidance in rubric["criteria"]
				],
			}
		)
