"""
Student / Course enrollment system.
Project topic: Sets in Formal Methods.

The system state is described with sets:

    students   : set of student ids
    courses    : set of course ids
    enrolled   : course id  -> set of student ids   (current class list)
    completed  : student id -> set of course ids    (passed courses)

Invariants (always true, checked after every change):
    I1  enrolled(c) is a subset of students
    I2  size of enrolled(c) <= capacity(c)
    I3  a student is never enrolled in a course he/she has already completed
    I4  prerequisites(c) is a subset of courses
    I5  every enrolled student has completed all prerequisites of the course
"""
from dataclasses import dataclass


# ---------------------------------------------------------------- errors
class EnrollmentError(Exception):
    """Base class: the request was invalid."""

class DuplicateError(EnrollmentError):
    """Student or course is already registered."""

class NotFoundError(EnrollmentError):
    """Student or course is not registered."""

class AlreadyEnrolledError(EnrollmentError):
    """Student is already enrolled in this course."""

class AlreadyCompletedError(EnrollmentError):
    """Student has already completed this course."""

class NotEnrolledError(EnrollmentError):
    """Student is not enrolled in this course."""

class CourseFullError(EnrollmentError):
    """Course has no free seats."""

class PrerequisiteNotMetError(EnrollmentError):
    """Student has not completed all prerequisites."""
    def __init__(self, missing):
        self.missing = frozenset(missing)   # prerequisites - completed
        super().__init__(f"missing prerequisites: {sorted(self.missing)}")

class InvariantViolation(Exception):
    """An invariant is broken. This is a bug in the code, not a user error."""


# ---------------------------------------------------------------- data
@dataclass(frozen=True)
class Student:
    id: str
    name: str


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    capacity: int
    prerequisites: frozenset = frozenset()

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")


# ---------------------------------------------------------------- service
class EnrollmentService:
    def __init__(self):
        self._students = {}    # student id -> Student
        self._courses = {}     # course id  -> Course
        self._enrolled = {}    # course id  -> set of student ids
        self._completed = {}   # student id -> set of course ids

    # ---- commands: change the state ------------------------------------
    def register_student(self, student):
        """Requires: student id is not registered yet."""
        if student.id in self._students:
            raise DuplicateError(f"student {student.id} already exists")
        self._students[student.id] = student
        self._completed[student.id] = set()
        self.check_invariants()

    def register_course(self, course):
        """Requires: course id is new, and all prerequisites are registered."""
        if course.id in self._courses:
            raise DuplicateError(f"course {course.id} already exists")
        unknown = course.prerequisites - self._courses.keys()
        if unknown:
            raise NotFoundError(f"unknown prerequisites: {sorted(unknown)}")
        self._courses[course.id] = course
        self._enrolled[course.id] = set()
        self.check_invariants()

    def enroll(self, student_id, course_id):
        """
        Requires: student is not enrolled in and has not completed the course,
                  has completed all prerequisites, and the course is not full.
        Ensures:  student is in the class list of the course.
        """
        student, course = self._get_student(student_id), self._get_course(course_id)
        if student_id in self._enrolled[course_id]:
            raise AlreadyEnrolledError(f"{student_id} is already in {course_id}")
        if course_id in self._completed[student_id]:
            raise AlreadyCompletedError(f"{student_id} already completed {course_id}")
        missing = course.prerequisites - self._completed[student_id]
        if missing:
            raise PrerequisiteNotMetError(missing)
        if len(self._enrolled[course_id]) >= course.capacity:
            raise CourseFullError(f"{course_id} is full")

        self._enrolled[course_id].add(student_id)
        self.check_invariants()

    def drop(self, student_id, course_id):
        """
        Requires: student is enrolled in the course.
        Ensures:  student is removed from the class list.
        """
        self._require_enrolled(student_id, course_id)
        self._enrolled[course_id].remove(student_id)
        self.check_invariants()

    def complete(self, student_id, course_id):
        """
        Requires: student is enrolled in the course.
        Ensures:  student is removed from the class list and
                  the course is added to the student's completed courses.
        """
        self._require_enrolled(student_id, course_id)
        self._enrolled[course_id].remove(student_id)
        self._completed[student_id].add(course_id)
        self.check_invariants()

    # ---- queries: read only, return immutable sets ----------------------
    def roster(self, course_id):
        """Students currently enrolled in the course."""
        self._get_course(course_id)
        return frozenset(self._enrolled[course_id])

    def completed_by(self, student_id):
        """Courses the student has completed."""
        self._get_student(student_id)
        return frozenset(self._completed[student_id])

    def students_in_either(self, course_a, course_b):
        """Union: students in course A or course B (or both)."""
        return self.roster(course_a) | self.roster(course_b)

    def students_in_both(self, course_a, course_b):
        """Intersection: students in course A and course B."""
        return self.roster(course_a) & self.roster(course_b)

    def students_only_in_first(self, course_a, course_b):
        """Difference: students in course A who are not in course B."""
        return self.roster(course_a) - self.roster(course_b)

    def roster_is_subset(self, course_a, course_b):
        """Subset: is every student of course A also in course B?"""
        return self.roster(course_a) <= self.roster(course_b)

    def rosters_are_disjoint(self, course_a, course_b):
        """Disjoint: do course A and course B have no student in common?"""
        return self.roster(course_a).isdisjoint(self.roster(course_b))

    def missing_prerequisites(self, student_id, course_id):
        """Difference: prerequisites of the course the student has not completed."""
        return self._get_course(course_id).prerequisites - self.completed_by(student_id)

    def can_take(self, student_id, course_id):
        """Subset: are all prerequisites completed? (capacity is not checked)"""
        return not self.missing_prerequisites(student_id, course_id)

    # ---- invariants ------------------------------------------------------
    def check_invariants(self):
        for course_id, course in self._courses.items():
            roster = self._enrolled[course_id]
            if not roster <= self._students.keys():
                raise InvariantViolation(f"I1 broken in {course_id}")
            if len(roster) > course.capacity:
                raise InvariantViolation(f"I2 broken in {course_id}")
            if not course.prerequisites <= self._courses.keys():
                raise InvariantViolation(f"I4 broken in {course_id}")
            for student_id in roster:
                done = self._completed[student_id]
                if course_id in done:
                    raise InvariantViolation(f"I3 broken: {student_id}, {course_id}")
                if not course.prerequisites <= done:
                    raise InvariantViolation(f"I5 broken: {student_id}, {course_id}")

    # ---- helpers ---------------------------------------------------------
    def _get_student(self, student_id):
        if student_id not in self._students:
            raise NotFoundError(f"student {student_id} not found")
        return self._students[student_id]

    def _get_course(self, course_id):
        if course_id not in self._courses:
            raise NotFoundError(f"course {course_id} not found")
        return self._courses[course_id]

    def _require_enrolled(self, student_id, course_id):
        self._get_student(student_id)
        self._get_course(course_id)
        if student_id not in self._enrolled[course_id]:
            raise NotEnrolledError(f"{student_id} is not in {course_id}")


# ---------------------------------------------------------------- demo
def build_demo():
    service = EnrollmentService()
    for student_id, name in [("s1", "Ali"), ("s2", "Sara"), ("s3", "Reza"), ("s4", "Mina")]:
        service.register_student(Student(student_id, name))

    service.register_course(Course("CS101", "Intro to Programming", capacity=3))
    service.register_course(Course("MATH101", "Discrete Math", capacity=3))
    service.register_course(Course("FM201", "Formal Methods", capacity=2,
                                   prerequisites=frozenset({"CS101", "MATH101"})))

    for student_id in ("s1", "s2", "s3"):
        service.enroll(student_id, "CS101")
    for student_id in ("s2", "s3", "s4"):
        service.enroll(student_id, "MATH101")
    return service


def main():
    service = build_demo()

    print("CS101 students       :", sorted(service.roster("CS101")))
    print("MATH101 students     :", sorted(service.roster("MATH101")))
    print("Union                :", sorted(service.students_in_either("CS101", "MATH101")))
    print("Intersection         :", sorted(service.students_in_both("CS101", "MATH101")))
    print("Only in CS101        :", sorted(service.students_only_in_first("CS101", "MATH101")))
    print("Disjoint?            :", service.rosters_are_disjoint("CS101", "MATH101"))

    print("s1 missing for FM201 :", sorted(service.missing_prerequisites("s1", "FM201")))
    try:
        service.enroll("s1", "FM201")
    except PrerequisiteNotMetError as error:
        print("s1 enroll in FM201   : rejected,", error)

    for course_id in ("CS101", "MATH101"):
        service.complete("s2", course_id)
    print("s2 can take FM201?   :", service.can_take("s2", "FM201"))
    service.enroll("s2", "FM201")
    print("FM201 students       :", sorted(service.roster("FM201")))


if __name__ == "__main__":
    main()
