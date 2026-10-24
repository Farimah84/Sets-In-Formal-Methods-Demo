import itertools
import unittest

from enrollment_system import (
    AlreadyCompletedError, AlreadyEnrolledError, Course, CourseFullError,
    DuplicateError, EnrollmentService, InvariantViolation, NotEnrolledError,
    NotFoundError, PrerequisiteNotMetError, Student, build_demo,
)

# Demo data:  CS101 = {s1, s2, s3}   MATH101 = {s2, s3, s4}   FM201 = {}
# FM201 requires CS101 and MATH101.


class EnrollmentRulesTest(unittest.TestCase):
    def setUp(self):
        self.service = build_demo()

    def test_enroll_adds_student_to_roster(self):
        self.assertIn("s1", self.service.roster("CS101"))

    def test_enroll_twice_is_rejected(self):
        with self.assertRaises(AlreadyEnrolledError):
            self.service.enroll("s1", "CS101")

    def test_missing_prerequisites_are_reported(self):
        with self.assertRaises(PrerequisiteNotMetError) as context:
            self.service.enroll("s1", "FM201")
        self.assertEqual(context.exception.missing, {"CS101", "MATH101"})

    def test_full_course_is_rejected(self):
        service = EnrollmentService()
        for student_id in ("a", "b", "c"):
            service.register_student(Student(student_id, student_id))
        service.register_course(Course("X", "X", capacity=2))
        service.enroll("a", "X")
        service.enroll("b", "X")
        with self.assertRaises(CourseFullError):
            service.enroll("c", "X")

    def test_complete_moves_student_from_roster_to_completed(self):
        self.service.complete("s1", "CS101")
        self.assertNotIn("s1", self.service.roster("CS101"))
        self.assertIn("CS101", self.service.completed_by("s1"))
        with self.assertRaises(AlreadyCompletedError):
            self.service.enroll("s1", "CS101")

    def test_drop_removes_student(self):
        self.service.drop("s1", "CS101")
        self.assertNotIn("s1", self.service.roster("CS101"))

    def test_drop_without_enrollment_is_rejected(self):
        with self.assertRaises(NotEnrolledError):
            self.service.drop("s1", "MATH101")

    def test_unknown_student_or_course_is_rejected(self):
        with self.assertRaises(NotFoundError):
            self.service.enroll("nobody", "CS101")
        with self.assertRaises(NotFoundError):
            self.service.roster("nothing")

    def test_duplicate_registration_is_rejected(self):
        with self.assertRaises(DuplicateError):
            self.service.register_student(Student("s1", "Ali"))
        with self.assertRaises(DuplicateError):
            self.service.register_course(Course("CS101", "Again", capacity=1))

    def test_unknown_prerequisite_is_rejected(self):
        with self.assertRaises(NotFoundError):
            self.service.register_course(
                Course("AI301", "AI", capacity=1, prerequisites=frozenset({"GHOST"})))

    def test_failed_command_does_not_change_state(self):
        before = self.service.roster("CS101")
        with self.assertRaises(AlreadyEnrolledError):
            self.service.enroll("s1", "CS101")
        self.assertEqual(self.service.roster("CS101"), before)


class SetQueriesTest(unittest.TestCase):
    def setUp(self):
        self.service = build_demo()

    def test_union_intersection_difference(self):
        s = self.service
        self.assertEqual(s.students_in_either("CS101", "MATH101"), {"s1", "s2", "s3", "s4"})
        self.assertEqual(s.students_in_both("CS101", "MATH101"), {"s2", "s3"})
        self.assertEqual(s.students_only_in_first("CS101", "MATH101"), {"s1"})
        self.assertEqual(s.students_only_in_first("MATH101", "CS101"), {"s4"})

    def test_subset_and_disjoint(self):
        s = self.service
        self.assertTrue(s.roster_is_subset("CS101", "CS101"))
        self.assertFalse(s.roster_is_subset("CS101", "MATH101"))
        self.assertTrue(s.roster_is_subset("FM201", "CS101"))      # empty set
        self.assertFalse(s.rosters_are_disjoint("CS101", "MATH101"))
        self.assertTrue(s.rosters_are_disjoint("CS101", "FM201"))

    def test_can_take_and_missing_prerequisites(self):
        s = self.service
        self.assertFalse(s.can_take("s2", "FM201"))
        self.assertEqual(s.missing_prerequisites("s2", "FM201"), {"CS101", "MATH101"})
        s.complete("s2", "CS101")
        self.assertEqual(s.missing_prerequisites("s2", "FM201"), {"MATH101"})
        s.complete("s2", "MATH101")
        self.assertTrue(s.can_take("s2", "FM201"))

    def test_queries_return_immutable_sets(self):
        self.assertIsInstance(self.service.roster("CS101"), frozenset)

    def test_set_laws_hold_for_every_pair_of_courses(self):
        s = self.service
        for a, b in itertools.permutations(["CS101", "MATH101", "FM201"], 2):
            union = s.students_in_either(a, b)
            both = s.students_in_both(a, b)
            only_a = s.students_only_in_first(a, b)
            self.assertEqual(union, s.students_in_either(b, a))
            self.assertEqual(both, s.students_in_both(b, a))
            self.assertEqual(len(union), len(s.roster(a)) + len(s.roster(b)) - len(both))
            self.assertEqual(only_a | both, s.roster(a))
            self.assertTrue(only_a.isdisjoint(both))


class InvariantsTest(unittest.TestCase):
    def test_broken_state_is_detected(self):
        service = build_demo()
        service._enrolled["FM201"].add("s1")    # s1 has no prerequisites: breaks I5
        with self.assertRaises(InvariantViolation):
            service.check_invariants()

    def test_course_capacity_must_be_positive(self):
        with self.assertRaises(ValueError):
            Course("X", "X", capacity=0)


if __name__ == "__main__":
    unittest.main()
