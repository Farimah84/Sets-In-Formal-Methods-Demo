import matplotlib.pyplot as plt
from matplotlib_venn import venn2

# 2) A small helper function to print a set in a consistent, readable way.
def show_set(label, items):
    print(f"{label}: {sorted(items)}")


# 3) Define two example sets.
# Set A contains students enrolled in the Programming course.
programming_students = {"Ali", "Sara", "Nima", "Mina"}

# Set B contains students enrolled in the Mathematics course.
math_students = {"Sara", "Nima", "Reza", "Leila"}


# 4) Perform the basic set operations.
# Union (A ∪ B): students who are in A, in B, or in both.
union_result = programming_students | math_students

# Intersection (A ∩ B): students who are in both A and B.
intersection_result = programming_students & math_students

# Difference (A − B): students in A but not in B.
difference_result = programming_students - math_students

# Subset (A ⊆ B): True if every member of A is also a member of B.
subset_result = programming_students.issubset(math_students)


# 5) Print the results so they can be discussed during the demo.
print("=== Basic Set Operations ===")
show_set("Programming students (A)", programming_students)
show_set("Mathematics students (B)", math_students)
show_set("Union (A | B)", union_result)
show_set("Intersection (A & B)", intersection_result)
show_set("Difference (A - B)", difference_result)
print(f"Is A a subset of B? {subset_result}")


# 6) Model the Student and Course concepts with sets.
# The set contains all students known to this small example system.
all_students = {"Ali", "Sara", "Nima", "Mina", "Reza", "Leila", "Omid"}

# Each course is associated with the set of students enrolled in it.
course_enrollments = {
    "Programming": programming_students,
    "Mathematics": math_students,
}

print("\n=== Student and Course Model ===")
show_set("All students in the system", all_students)

for course_name, enrolled_students in course_enrollments.items():
    show_set(f"Students enrolled in {course_name}", enrolled_students)

# A simple consistency check:
# every student enrolled in a course should exist in the system's student set.
for course_name, enrolled_students in course_enrollments.items():
    if enrolled_students.issubset(all_students):
        print(f"Check passed: every student in {course_name} exists in all_students.")
    else:
        print(f"Check FAILED: {course_name} contains an unknown student.")


# 7) Draw and save a Venn diagram for the two course-enrollment sets.
venn2(
    [programming_students, math_students],
    set_labels=("Programming", "Mathematics"),
)
plt.title("Student Enrollment: Programming vs Mathematics")
plt.tight_layout()
plt.savefig("venn_courses.png", dpi=200, bbox_inches="tight")
print("\nVenn diagram saved as: venn_courses.png")

# Show the diagram in a window when the environment supports it.
plt.show()