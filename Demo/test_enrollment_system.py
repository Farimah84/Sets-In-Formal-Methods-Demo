import itertools
import unittest

from enrollment_system import *
from enrollment_system import build_demo

S = StudentId
C = CourseId


class EnrollmentRules(unittest.TestCase):
    def setUp(self):
        self.svc = build_demo()

    def test_enroll_adds_to_roster(self):
        self.assertIn(S("s1"), self.svc.roster(C("CS101")))

    def test_duplicate_enrollment_rejected(self):
        with self.assertRaises(AlreadyEnrolledError):
            self.svc.enroll(S("s1"), C("CS101"))

    def test_prerequisite_enforced_and_reports_missing_set(self):
        with self.assertRaises(PrerequisiteNotMetError) as ctx:
            self.svc.enroll(S("s1"), C("FM201"))
        self.assertEqual(ctx.exception.missing, {C("CS101"), C("MATH101")})

    def test_capacity_enforced(self):
        svc = EnrollmentService()
        for i in range(3):
            svc.register_student(Student(S(f"x{i}"), f"X{i}"))
        svc.register_course(Course(C("A"), "A", capacity=2))
        svc.enroll(S("x0"), C("A"))
        svc.enroll(S("x1"), C("A"))
        with self.assertRaises(CourseFullError):
            svc.enroll(S("x2"), C("A"))

    def test_complete_moves_student_between_sets(self):
        self.svc.complete(S("s1"), C("CS101"))
        self.assertNotIn(S("s1"), self.svc.roster(C("CS101")))
        self.assertIn(C("CS101"), self.svc.completed_by(S("s1")))
        with self.assertRaises(AlreadyCompletedError):
            self.svc.enroll(S("s1"), C("CS101"))

    def test_drop_requires_enrollment(self):
        with self.assertRaises(NotEnrolledError):
            self.svc.drop(S("s1"), C("MATH101"))

    def test_unknown_entities(self):
        with self.assertRaises(UnknownStudentError):
            self.svc.enroll(S("nope"), C("CS101"))
        with self.assertRaises(UnknownCourseError):
            self.svc.roster(C("nope"))

    def test_failed_command_leaves_state_unchanged(self):
        before = self.svc.roster(C("CS101"))
        with self.assertRaises(AlreadyEnrolledError):
            self.svc.enroll(S("s1"), C("CS101"))
        self.assertEqual(before, self.svc.roster(C("CS101")))

    def test_audit_log_is_append_only_snapshot(self):
        n = len(self.svc.audit_log)
        self.svc.drop(S("s1"), C("CS101"))
        self.assertEqual(len(self.svc.audit_log), n + 1)
        self.assertEqual(self.svc.audit_log[-1].kind, EventKind.DROPPED)

    def test_queries_return_immutable_sets(self):
        self.assertIsInstance(self.svc.roster(C("CS101")), frozenset)


class SetQueries(unittest.TestCase):
    def setUp(self):
        self.svc = build_demo()
        self.cs, self.m = C("CS101"), C("MATH101")

    def test_union_intersection_difference(self):
        self.assertEqual(self.svc.students_in_either(self.cs, self.m),
                         {S("s1"), S("s2"), S("s3"), S("s4")})
        self.assertEqual(self.svc.students_in_both(self.cs, self.m),
                         {S("s2"), S("s3")})
        self.assertEqual(self.svc.students_only_in(self.cs, self.m), {S("s1")})

    def test_subset_and_disjoint(self):
        self.assertFalse(self.svc.is_roster_subset(self.cs, self.m))
        self.assertFalse(self.svc.are_rosters_disjoint(self.cs, self.m))
        self.assertTrue(self.svc.is_roster_subset(self.cs, self.cs))

    def test_generalised_operations(self):
        self.assertEqual(len(self.svc.students_in_any([self.cs, self.m])), 4)
        self.assertEqual(self.svc.students_in_all([self.cs, self.m]),
                         {S("s2"), S("s3")})
        self.assertEqual(self.svc.students_in_all([]), frozenset())

    def test_eligibility(self):
        for sid in ("s2",):
            for c in (self.cs, self.m):
                self.svc.complete(S(sid), c)
        self.assertTrue(self.svc.can_take(S("s2"), C("FM201")))
        self.assertEqual(self.svc.eligible_courses(S("s2")), {C("FM201")})
        self.assertFalse(self.svc.can_take(S("s1"), C("FM201")))

    def test_set_laws_hold_for_every_pair_of_courses(self):
        """The system's queries must satisfy the algebra they model."""
        ids = [C("CS101"), C("MATH101"), C("FM201")]
        for a, b in itertools.permutations(ids, 2):
            u = self.svc.students_in_either(a, b)
            i = self.svc.students_in_both(a, b)
            d = self.svc.students_only_in(a, b)
            self.assertEqual(u, self.svc.students_in_either(b, a))      # commutative
            self.assertEqual(i, self.svc.students_in_both(b, a))
            self.assertEqual(len(u), len(self.svc.roster(a)) + len(self.svc.roster(b)) - len(i))
            self.assertEqual(d | i, self.svc.roster(a))                 # partition of A
            self.assertTrue(d.isdisjoint(i))


class Invariants(unittest.TestCase):
    def test_tampering_is_detected(self):
        svc = build_demo()
        svc._enrolled[C("FM201")].add(S("s1"))   # simulate a bug: skips prereq check
        with self.assertRaises(InvariantViolation):
            svc._verify()

    def test_value_object_validation(self):
        with self.assertRaises(ValueError):
            Course(C("X"), "X", capacity=0)
        with self.assertRaises(ValueError):
            Course(C("X"), "X", capacity=1, prerequisites=frozenset({C("X")}))


if __name__ == "__main__":
    unittest.main()
