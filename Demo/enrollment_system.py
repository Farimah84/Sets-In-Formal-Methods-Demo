"""
Student/Course enrollment system -- "Sets in Formal Methods" demo.

Software-engineering view of the topic:
  * Sets are the *state model* of the system (like a Z / B specification),
    not loose math exercises.
  * Every operation has explicit PRECONDITIONS (checked, raise domain errors),
    POSTCONDITIONS (asserted) and a class INVARIANT (checked after each change).
  * Set operations (union, intersection, difference, subset, disjoint)
    appear as real business queries.

State model (Z-style):
    students   : set of StudentId
    courses    : set of CourseId
    enrolled   : CourseId  -> set of StudentId        (current roster)
    completed  : StudentId -> set of CourseId         (passed courses)

Invariants:
    I1  for all c: enrolled(c) is a subset of students
    I2  for all c: |enrolled(c)| <= capacity(c)
    I3  for all s, c: not (s in enrolled(c) and c in completed(s))
    I4  for all c: prerequisites(c) is a subset of courses
    I5  for all c, s in enrolled(c): prerequisites(c) is a subset of completed(s)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Iterable, NewType

StudentId = NewType("StudentId", str)
CourseId = NewType("CourseId", str)


# --------------------------------------------------------------------------
# Domain errors (one per violated precondition -> easy to handle and test)
# --------------------------------------------------------------------------
class EnrollmentError(Exception):
    """Base class for all domain errors."""


class DuplicateEntityError(EnrollmentError): ...
class UnknownStudentError(EnrollmentError): ...
class UnknownCourseError(EnrollmentError): ...
class AlreadyEnrolledError(EnrollmentError): ...
class AlreadyCompletedError(EnrollmentError): ...
class NotEnrolledError(EnrollmentError): ...
class CourseFullError(EnrollmentError): ...


class PrerequisiteNotMetError(EnrollmentError):
    def __init__(self, student_id: StudentId, course_id: CourseId,
                 missing: FrozenSet[CourseId]):
        self.missing = missing  # set difference: prerequisites - completed
        super().__init__(
            f"{student_id} cannot take {course_id}; missing: {sorted(missing)}"
        )


class InvariantViolation(AssertionError):
    """Raised when the system state breaks a documented invariant (a bug)."""


# --------------------------------------------------------------------------
# Value objects (immutable => safe to share, hash, and use inside sets)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Student:
    id: StudentId
    name: str


@dataclass(frozen=True)
class Course:
    id: CourseId
    title: str
    capacity: int
    prerequisites: FrozenSet[CourseId] = frozenset()

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.id in self.prerequisites:
            raise ValueError("a course cannot be its own prerequisite")


class EventKind(Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Event:
    """Audit-log entry. The log is append-only."""
    kind: EventKind
    student_id: StudentId
    course_id: CourseId


# --------------------------------------------------------------------------
# Service (aggregate root): the only place where state may change
# --------------------------------------------------------------------------
class EnrollmentService:
    def __init__(self, check_invariants: bool = True) -> None:
        self._students: dict[StudentId, Student] = {}
        self._courses: dict[CourseId, Course] = {}
        self._enrolled: dict[CourseId, set[StudentId]] = {}
        self._completed: dict[StudentId, set[CourseId]] = {}
        self._log: list[Event] = []
        self._check = check_invariants

    # ---- registration ----------------------------------------------------
    def register_student(self, student: Student) -> None:
        if student.id in self._students:
            raise DuplicateEntityError(f"student {student.id} exists")
        self._students[student.id] = student
        self._completed[student.id] = set()
        self._verify()

    def register_course(self, course: Course) -> None:
        if course.id in self._courses:
            raise DuplicateEntityError(f"course {course.id} exists")
        unknown = course.prerequisites - self._courses.keys()  # set difference
        if unknown:
            raise UnknownCourseError(f"unknown prerequisites: {sorted(unknown)}")
        self._courses[course.id] = course
        self._enrolled[course.id] = set()
        self._verify()

    # ---- commands (state changes) ---------------------------------------
    def enroll(self, sid: StudentId, cid: CourseId) -> None:
        course = self._course(cid)
        self._student(sid)

        # Preconditions
        if sid in self._enrolled[cid]:
            raise AlreadyEnrolledError(f"{sid} already in {cid}")
        if cid in self._completed[sid]:
            raise AlreadyCompletedError(f"{sid} already completed {cid}")
        missing = course.prerequisites - self._completed[sid]  # not a subset
        if missing:
            raise PrerequisiteNotMetError(sid, cid, frozenset(missing))
        if len(self._enrolled[cid]) >= course.capacity:
            raise CourseFullError(f"{cid} is full")

        before = len(self._enrolled[cid])
        self._enrolled[cid].add(sid)

        # Postcondition
        assert sid in self._enrolled[cid] and len(self._enrolled[cid]) == before + 1
        self._log.append(Event(EventKind.ENROLLED, sid, cid))
        self._verify()

    def drop(self, sid: StudentId, cid: CourseId) -> None:
        self._course(cid)
        self._student(sid)
        if sid not in self._enrolled[cid]:
            raise NotEnrolledError(f"{sid} is not in {cid}")
        self._enrolled[cid].remove(sid)
        assert sid not in self._enrolled[cid]
        self._log.append(Event(EventKind.DROPPED, sid, cid))
        self._verify()

    def complete(self, sid: StudentId, cid: CourseId) -> None:
        """Student passes the course: moves from enrolled(c) to completed(s)."""
        self._course(cid)
        self._student(sid)
        if sid not in self._enrolled[cid]:
            raise NotEnrolledError(f"{sid} is not in {cid}")
        self._enrolled[cid].remove(sid)
        self._completed[sid].add(cid)
        assert sid not in self._enrolled[cid] and cid in self._completed[sid]
        self._log.append(Event(EventKind.COMPLETED, sid, cid))
        self._verify()

    # ---- queries (pure, return immutable frozensets) ----------------------
    def roster(self, cid: CourseId) -> FrozenSet[StudentId]:
        self._course(cid)
        return frozenset(self._enrolled[cid])

    def completed_by(self, sid: StudentId) -> FrozenSet[CourseId]:
        self._student(sid)
        return frozenset(self._completed[sid])

    def students_in_either(self, a: CourseId, b: CourseId) -> FrozenSet[StudentId]:
        """UNION: e.g. who must be notified about a room change in A or B."""
        return self.roster(a) | self.roster(b)

    def students_in_both(self, a: CourseId, b: CourseId) -> FrozenSet[StudentId]:
        """INTERSECTION: e.g. students with an exam-schedule conflict risk."""
        return self.roster(a) & self.roster(b)

    def students_only_in(self, a: CourseId, b: CourseId) -> FrozenSet[StudentId]:
        """DIFFERENCE: e.g. students who would be affected if only A is cancelled."""
        return self.roster(a) - self.roster(b)

    def students_in_any(self, cids: Iterable[CourseId]) -> FrozenSet[StudentId]:
        """Generalised union over many courses."""
        return frozenset().union(*(self.roster(c) for c in cids))

    def students_in_all(self, cids: Iterable[CourseId]) -> FrozenSet[StudentId]:
        """Generalised intersection; empty input -> empty set (no vacuous 'everyone')."""
        rosters = [self.roster(c) for c in cids]
        return frozenset.intersection(*rosters) if rosters else frozenset()

    def is_roster_subset(self, a: CourseId, b: CourseId) -> bool:
        """SUBSET: is every student of A also in B? (e.g. can A and B be merged?)"""
        return self.roster(a) <= self.roster(b)

    def are_rosters_disjoint(self, a: CourseId, b: CourseId) -> bool:
        return self.roster(a).isdisjoint(self.roster(b))

    def missing_prerequisites(self, sid: StudentId, cid: CourseId) -> FrozenSet[CourseId]:
        return self._course(cid).prerequisites - self.completed_by(sid)

    def can_take(self, sid: StudentId, cid: CourseId) -> bool:
        """SUBSET: prerequisites(c) is a subset of completed(s)."""
        return self._course(cid).prerequisites <= self.completed_by(sid)

    def eligible_courses(self, sid: StudentId) -> FrozenSet[CourseId]:
        """Set comprehension: courses the student may enroll in right now."""
        done = self.completed_by(sid)
        return frozenset(
            c.id for c in self._courses.values()
            if c.id not in done
            and sid not in self._enrolled[c.id]
            and c.prerequisites <= done
            and len(self._enrolled[c.id]) < c.capacity
        )

    @property
    def audit_log(self) -> tuple[Event, ...]:
        return tuple(self._log)  # immutable snapshot

    # ---- internals --------------------------------------------------------
    def _student(self, sid: StudentId) -> Student:
        try:
            return self._students[sid]
        except KeyError:
            raise UnknownStudentError(sid) from None

    def _course(self, cid: CourseId) -> Course:
        try:
            return self._courses[cid]
        except KeyError:
            raise UnknownCourseError(cid) from None

    def _verify(self) -> None:
        """Class invariant I1..I5. Disable in production if too costly."""
        if not self._check:
            return
        all_students = self._students.keys()
        all_courses = self._courses.keys()
        for cid, course in self._courses.items():
            roster = self._enrolled[cid]
            if not roster <= all_students:                                   # I1
                raise InvariantViolation(f"I1 broken in {cid}")
            if len(roster) > course.capacity:                                # I2
                raise InvariantViolation(f"I2 broken in {cid}")
            if not course.prerequisites <= all_courses:                      # I4
                raise InvariantViolation(f"I4 broken in {cid}")
            for sid in roster:
                if cid in self._completed[sid]:                              # I3
                    raise InvariantViolation(f"I3 broken: {sid}/{cid}")
                if not course.prerequisites <= self._completed[sid]:         # I5
                    raise InvariantViolation(f"I5 broken: {sid}/{cid}")


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------
def build_demo() -> EnrollmentService:
    svc = EnrollmentService()
    for sid, name in [("s1", "Ali"), ("s2", "Sara"), ("s3", "Reza"), ("s4", "Mina")]:
        svc.register_student(Student(StudentId(sid), name))

    svc.register_course(Course(CourseId("CS101"), "Intro to Programming", capacity=3))
    svc.register_course(Course(CourseId("MATH101"), "Discrete Math", capacity=3))
    svc.register_course(Course(
        CourseId("FM201"), "Formal Methods", capacity=2,
        prerequisites=frozenset({CourseId("CS101"), CourseId("MATH101")})))

    for sid in ("s1", "s2", "s3"):
        svc.enroll(StudentId(sid), CourseId("CS101"))
    for sid in ("s2", "s3", "s4"):
        svc.enroll(StudentId(sid), CourseId("MATH101"))
    return svc


def main() -> None:
    svc = build_demo()
    cs, math_, fm = CourseId("CS101"), CourseId("MATH101"), CourseId("FM201")

    print("Union        :", sorted(svc.students_in_either(cs, math_)))
    print("Intersection :", sorted(svc.students_in_both(cs, math_)))
    print("Difference   :", sorted(svc.students_only_in(cs, math_)))
    print("Disjoint?    :", svc.are_rosters_disjoint(cs, math_))

    # s2 and s3 pass both prerequisites -> subset check becomes true
    for sid in ("s2", "s3"):
        for c in (cs, math_):
            svc.complete(StudentId(sid), c)
    print("s2 can take FM201:", svc.can_take(StudentId("s2"), fm))
    print("s1 missing       :", sorted(svc.missing_prerequisites(StudentId("s1"), fm)))
    print("s2 eligible      :", sorted(svc.eligible_courses(StudentId("s2"))))

    try:
        svc.enroll(StudentId("s1"), fm)
    except PrerequisiteNotMetError as e:
        print("Rejected:", e)

    print("Audit log size   :", len(svc.audit_log))


if __name__ == "__main__":
    main()
