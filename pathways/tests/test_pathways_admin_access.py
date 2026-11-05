# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pathways Admin has full access to Pathways, including Roles &
Permissions, but cannot reach beyond Pathways or weaken its own role."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from pathways.api import access
from pathways.permissions import has_duty


def _user(label, roles=()):
	email = f"admin-access-{label}-{frappe.generate_hash(length=6)}@example.com"
	frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "user_type": "System User", "send_welcome_email": 0}).insert(ignore_permissions=True)
	if roles:
		user = frappe.get_doc("User", email)
		user.add_roles(*roles)
	return email


class TestPathwaysAdminAccess(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.admin = _user("admin", ("Pathways Admin",))
		self.staff = _user("staff")

	def tearDown(self):
		frappe.set_user("Administrator")

	def _as_admin(self, fn, *args, **kwargs):
		frappe.set_user(self.admin)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_full_access_to_pathways_records(self):
		frappe.set_user(self.admin)
		try:
			for doctype, ptypes in {
				"Post-Interview Green Sheet": ("read", "write", "create", "submit", "cancel"),
				"Pre-Recruitment Green Sheet": ("read", "write", "create", "submit", "cancel"),
				"Application": ("read", "write", "create", "delete"),
				"Communication Log": ("read", "export"),
				"Application Status History": ("read", "export"),
				"Pathways Settings": ("read", "write"),
			}.items():
				for ptype in ptypes:
					self.assertTrue(frappe.has_permission(doctype, ptype), f"{doctype}: {ptype}")
			from pathways.pathways.doctype.job_opening.job_opening import can_override_status

			self.assertTrue(can_override_status())
			self.assertTrue(has_duty("offer_reviewer_roles"))
			self.assertTrue(has_duty("document_verifier_roles"))
			me = access.get_my_access()
			self.assertTrue(me["can_manage_access"])
			for menu in ("jobs", "applications", "interviews", "offers", "documents", "communications", "reports", "master_setup"):
				self.assertIn(menu, me["menu"])
		finally:
			frappe.set_user("Administrator")

	def test_manages_pathways_users_and_roles(self):
		self._as_admin(access.assign_role, self.staff, "Pathways Recruiter")
		self.assertIn("Pathways Recruiter", frappe.get_roles(self.staff))
		self._as_admin(access.unassign_role, self.staff, "Pathways Recruiter")
		self.assertNotIn("Pathways Recruiter", frappe.get_roles(self.staff))
		# Another administrator: allowed.
		self._as_admin(access.assign_role, self.staff, "Pathways Admin")
		self._as_admin(access.unassign_role, self.staff, "Pathways Admin")
		with patch("pathways.api.access.send_staff_welcome"):
			name = self._as_admin(access.create_staff_user, f"new-{frappe.generate_hash(length=6)}@example.com", "New", roles=["Pathways Recruiter", "System Manager"])
		roles = frappe.get_roles(name)
		self.assertIn("Pathways Recruiter", roles)
		self.assertNotIn("System Manager", roles)  # not a Pathways role: dropped
		self.assertTrue(self._as_admin(access.get_access_matrix)["roles"])
		self._as_admin(access.set_role_permission, "Application Draft", "Pathways Recruiter", "read", 1)
		new_role = f"Pathways Test {frappe.generate_hash(length=5)}"
		self.assertEqual(self._as_admin(access.create_role, new_role), new_role)

	def test_cannot_reach_beyond_pathways_or_weaken_its_own_role(self):
		outside = f"Outside Role {frappe.generate_hash(length=5)}"
		frappe.get_doc({"doctype": "Role", "role_name": outside}).insert(ignore_permissions=True)
		self.assertRaises(frappe.PermissionError, self._as_admin, access.create_role, outside)
		self.assertRaises(frappe.ValidationError, self._as_admin, access.assign_role, self.staff, "System Manager")
		self.assertRaises(frappe.ValidationError, self._as_admin, access.create_role, "System Manager")
		self.assertRaises(frappe.PermissionError, self._as_admin, access.set_role_permission, "Application", "Pathways Admin", "read", 0)
		self.assertRaises(frappe.PermissionError, self._as_admin, access.remove_role, "Pathways Admin")
		self.assertRaises(frappe.ValidationError, self._as_admin, access.unassign_role, self.admin, "Pathways Admin")
		self.assertRaises(frappe.ValidationError, self._as_admin, access.set_role_permission, "User", "Pathways Recruiter", "read", 1)
		self.assertIn("Pathways Admin", frappe.get_roles(self.admin))

	def test_system_manager_keeps_full_control(self):
		outside = f"Outside Role {frappe.generate_hash(length=5)}"
		frappe.get_doc({"doctype": "Role", "role_name": outside}).insert(ignore_permissions=True)
		self.assertEqual(access.create_role(outside), outside)  # Administrator holds System Manager
		access.set_role_permission("Application Draft", "Pathways Admin", "read", 1)
		frappe.set_user(self.staff)
		try:
			self.assertRaises(frappe.PermissionError, access.get_access_matrix)  # no Pathways Admin, no System Manager
		finally:
			frappe.set_user("Administrator")
