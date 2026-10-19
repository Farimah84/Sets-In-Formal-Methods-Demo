# مستندات پروژه: سیستم ثبت‌نام دانشجو و درس
### مدل‌سازی «مجموعه‌ها در روش‌های صوری» از دید مهندسی نرم‌افزار

| | |
|---|---|
| **درس** | روش‌های صوری در مهندسی نرم‌افزار (Formal Methods in Software Engineering) |
| **موضوع** | مجموعه‌ها در روش‌های صوری: Set، Subset، Union، Intersection، Difference |
| **زبان پیاده‌سازی** | Python 3.10 یا بالاتر (بدون هیچ وابستگی خارجی) |
| **فایل‌ها** | `enrollment_system.py` (کد اصلی)، `test_enrollment_system.py` (تست‌ها) |

---

## فهرست

1. [مقدمه و هدف](#1-مقدمه-و-هدف)
2. [نصب و اجرا](#2-نصب-و-اجرا)
3. [نمای کلی معماری](#3-نمای-کلی-معماری)
4. [مدل صوری حالت سیستم](#4-مدل-صوری-حالت-سیستم)
5. [ناورداها (Invariants)](#5-ناورداها-invariants)
6. [مدل دامنه (Domain Model)](#6-مدل-دامنه-domain-model)
7. [خطاهای دامنه‌ای](#7-خطاهای-دامنهای)
8. [مرجع کامل API](#8-مرجع-کامل-api)
9. [نگاشت عملیات مجموعه‌ای به سناریوهای واقعی](#9-نگاشت-عملیات-مجموعهای-به-سناریوهای-واقعی)
10. [تصمیم‌های طراحی](#10-تصمیمهای-طراحی)
11. [تست‌ها](#11-تستها)
12. [اجرای نمونه (Demo)](#12-اجرای-نمونه-demo)
13. [محدودیت‌ها](#13-محدودیتها)
14. [راه‌های توسعه](#14-راههای-توسعه)
15. [واژه‌نامه](#15-واژهنامه)

---

## 1. مقدمه و هدف

### مسئله
در درس روش‌های صوری، مجموعه‌ها معمولاً با مثال‌های ریاضی ساده (مثل «اجتماع دو مجموعهٔ عدد») معرفی می‌شوند. هدف این پروژه نشان دادن این است که **مجموعه‌ها در عمل ابزار مدل‌سازی نرم‌افزارند**: همان کاری که در زبان‌های مشخصات مثل Z و B انجام می‌شود.

### ایدهٔ اصلی
یک سیستم ثبت‌نام دانشگاهی ساخته شده که:

- **حالت (state) سیستم** را با مجموعه‌ها و نگاشت‌ها مدل می‌کند.
- **قواعد کسب‌وکار** (پیش‌نیاز، ظرفیت و غیره) را به‌صورت پیش‌شرط، پس‌شرط و ناوردا بیان و در زمان اجرا بررسی می‌کند.
- **عملیات مجموعه‌ای** را به‌عنوان کوئری‌های واقعی دامنه ارائه می‌دهد، نه تمرین ریاضی.
- با **تست‌ها** نشان می‌دهد پیاده‌سازی با مشخصات صوری می‌خواند.

### مفاهیم مجموعه‌ای که پوشش داده می‌شوند

| مفهوم | نماد ریاضی | معادل در پایتون | کاربرد در پروژه |
|---|---|---|---|
| مجموعه | `S` | `set` / `frozenset` | لیست دانشجویان یک درس |
| اجتماع | `A ∪ B` | `a \| b` | دانشجویان حداقل یکی از دو درس |
| اشتراک | `A ∩ B` | `a & b` | دانشجویان هر دو درس |
| تفاضل | `A \ B` | `a - b` | دانشجویان فقط درس A، پیش‌نیازهای کم‌شده |
| زیرمجموعه | `A ⊆ B` | `a <= b` | بررسی پیش‌نیازها |
| مجزا بودن | `A ∩ B = ∅` | `a.isdisjoint(b)` | دو کلاس بدون دانشجوی مشترک |
| اجتماع/اشتراک تعمیم‌یافته | `⋃ Aᵢ` ، `⋂ Aᵢ` | `union(*...)` ، `intersection(*...)` | چند درس همزمان |
| تعریف مجموعه با شرط | `{x ∣ P(x)}` | set comprehension | درس‌های قابل انتخاب |

---

## 2. نصب و اجرا

### پیش‌نیازها
فقط **Python 3.10+** لازم است. هیچ پکیجی نصب نمی‌شود.

### اجرای دمو
```bash
python enrollment_system.py
```

### اجرای تست‌ها
```bash
python -m unittest -v
```
دو فایل باید در یک پوشه باشند، چون فایل تست کد اصلی را `import` می‌کند.

### استفاده به‌عنوان کتابخانه
```python
from enrollment_system import *

svc = EnrollmentService()
svc.register_student(Student(StudentId("s1"), "Ali"))
svc.register_course(Course(CourseId("CS101"), "Intro to Programming", capacity=30))
svc.enroll(StudentId("s1"), CourseId("CS101"))

print(svc.roster(CourseId("CS101")))   # frozenset({'s1'})
```

---

## 3. نمای کلی معماری

```
┌────────────────────────────────────────────────────────┐
│                    EnrollmentService                   │  ← تنها نقطهٔ تغییر state
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Commands    │  │   Queries    │  │  _verify()   │  │
│  │ enroll/drop/ │  │ roster, ∪, ∩,│  │ ناورداهای    │  │
│  │ complete ... │  │ \, ⊆ ...     │  │ I1..I5       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
│         │ تغییر           │ فقط خواندن                 │
│  ┌──────▼─────────────────▼──────────────────────────┐ │
│  │ State: _students, _courses, _enrolled,            │ │
│  │        _completed, _log                           │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
        ▲ استفاده می‌کند از
┌───────┴──────────────────────────────────────────┐
│ Value Objects (تغییرناپذیر): Student, Course,    │
│ Event, StudentId, CourseId                       │
└──────────────────────────────────────────────────┘
```

### لایه‌ها

| لایه | اجزا | مسئولیت |
|---|---|---|
| **اشیای ارزشی** | `Student`, `Course`, `Event`, `EventKind`, `StudentId`, `CourseId` | دادهٔ تغییرناپذیر و اعتبارسنجی ذاتی |
| **سرویس (Aggregate Root)** | `EnrollmentService` | نگهداری state، اجرای دستورها و پاسخ به کوئری‌ها |
| **خطاها** | سلسله‌مراتب `EnrollmentError` | گزارش دقیق نقض پیش‌شرط‌ها |
| **دمو** | `build_demo()`, `main()` | نمونهٔ اجرا |

### اصل جداسازی دستور و کوئری (CQS)
- **دستورها** (`register_*`, `enroll`, `drop`, `complete`) state را تغییر می‌دهند و چیزی برنمی‌گردانند.
- **کوئری‌ها** (`roster`, `students_in_either` و غیره) هیچ اثر جانبی ندارند و `frozenset` یا `bool` برمی‌گردانند.

---

## 4. مدل صوری حالت سیستم

مدل به سبک Z نوشته شده است. حالت سیستم از چهار جزء تشکیل می‌شود:

```
students   : P StudentId                       -- مجموعهٔ دانشجویان ثبت‌شده
courses    : P CourseId                        -- مجموعهٔ درس‌های ثبت‌شده
enrolled   : CourseId  → P StudentId           -- فهرست فعلی هر درس
completed  : StudentId → P CourseId            -- درس‌های گذرانده‌شدهٔ هر دانشجو
```

به‌همراه دو تابع ثابت برای هر درس:
```
capacity       : CourseId → N₁                 -- ظرفیت (عدد مثبت)
prerequisites  : CourseId → P CourseId         -- پیش‌نیازها
```

### نگاشت به کد

| مدل صوری | فیلد در کد | نوع |
|---|---|---|
| `students` | `_students` | `dict[StudentId, Student]` (کلیدها همان مجموعه‌اند) |
| `courses` | `_courses` | `dict[CourseId, Course]` |
| `enrolled` | `_enrolled` | `dict[CourseId, set[StudentId]]` |
| `completed` | `_completed` | `dict[StudentId, set[CourseId]]` |
| `capacity`, `prerequisites` | فیلدهای `Course` | `int`, `frozenset[CourseId]` |
| تاریخچه | `_log` | `list[Event]` |

---

## 5. ناورداها (Invariants)

ناوردا شرطی است که **همیشه** (قبل و بعد از هر عملیات) باید برقرار باشد. متد `_verify()` بعد از هر دستور همهٔ آن‌ها را چک می‌کند و در صورت نقض `InvariantViolation` می‌دهد.

| شناسه | بیان صوری | معنی |
|---|---|---|
| **I1** | `∀ c ∈ courses: enrolled(c) ⊆ students` | فقط دانشجوی ثبت‌شده می‌تواند در درس باشد |
| **I2** | `∀ c ∈ courses: #enrolled(c) ≤ capacity(c)` | ظرفیت هیچ درسی سرریز نمی‌شود |
| **I3** | `∀ s, c: ¬(s ∈ enrolled(c) ∧ c ∈ completed(s))` | کسی همزمان در درس و گذرانندهٔ همان درس نیست |
| **I4** | `∀ c ∈ courses: prerequisites(c) ⊆ courses` | پیش‌نیازها همیشه درس‌های معتبرند |
| **I5** | `∀ c, ∀ s ∈ enrolled(c): prerequisites(c) ⊆ completed(s)` | هر دانشجوی ثبت‌نام‌شده پیش‌نیازها را گذرانده است |

### چرا I5 همیشه برقرار می‌ماند؟
مجموعهٔ `completed(s)` فقط **بزرگ می‌شود** و هیچ عملیاتی از آن عضوی حذف نمی‌کند. پس اگر هنگام ثبت‌نام `prerequisites(c) ⊆ completed(s)` برقرار بوده، بعداً هم برقرار می‌ماند.

### نکتهٔ مهم دربارهٔ حلقه در پیش‌نیازها
چون هنگام `register_course` همهٔ پیش‌نیازها باید **از قبل** ثبت شده باشند (I4) و درس نمی‌تواند پیش‌نیاز خودش باشد، ساختار پیش‌نیازها **به‌صورت ساختاری یک گراف بدون دور (DAG)** است و بن‌بست پیش‌نیازی (A پیش‌نیاز B و B پیش‌نیاز A) ممکن نیست.

---

## 6. مدل دامنه (Domain Model)

### 6.1 انواع شناسه
```python
StudentId = NewType("StudentId", str)
CourseId  = NewType("CourseId", str)
```
`NewType` باعث می‌شود ابزارهای بررسی نوع (مثل mypy) جلوی اشتباه گرفتن شناسهٔ دانشجو با شناسهٔ درس را بگیرند، بدون هزینهٔ زمان اجرا.

### 6.2 `Student`
```python
@dataclass(frozen=True)
class Student:
    id: StudentId
    name: str
```
تغییرناپذیر و hashable است.

### 6.3 `Course`
```python
@dataclass(frozen=True)
class Course:
    id: CourseId
    title: str
    capacity: int
    prerequisites: FrozenSet[CourseId] = frozenset()
```
**اعتبارسنجی در `__post_init__`:**

| شرط | خطا |
|---|---|
| `capacity <= 0` | `ValueError` |
| `id in prerequisites` | `ValueError` |

### 6.4 `EventKind` و `Event`
```python
class EventKind(Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"

@dataclass(frozen=True)
class Event:
    kind: EventKind
    student_id: StudentId
    course_id: CourseId
```
هر دستور موفق یک `Event` به لاگ اضافه می‌کند. لاگ **فقط‌افزودنی** است.

---

## 7. خطاهای دامنه‌ای

همهٔ خطاها از `EnrollmentError` ارث می‌برند، بنابراین می‌توان با یک `except EnrollmentError` همه را گرفت یا هر کدام را جدا مدیریت کرد.

| خطا | چه زمانی رخ می‌دهد |
|---|---|
| `DuplicateEntityError` | ثبت دانشجو یا درسی که قبلاً ثبت شده |
| `UnknownStudentError` | دانشجو وجود ندارد |
| `UnknownCourseError` | درس وجود ندارد (یا پیش‌نیاز ثبت‌نشده) |
| `AlreadyEnrolledError` | دانشجو هم‌اکنون در این درس است |
| `AlreadyCompletedError` | دانشجو این درس را قبلاً گذرانده |
| `NotEnrolledError` | حذف یا اتمام درسی که دانشجو در آن نیست |
| `PrerequisiteNotMetError` | پیش‌نیازها کامل نیست. صفت `missing` مجموعهٔ درس‌های کم‌شده است |
| `CourseFullError` | ظرفیت درس پر است |
| `InvariantViolation` | یکی از ناورداها شکسته شده (نشانهٔ **باگ**، نه خطای کاربر) |

> `InvariantViolation` از `AssertionError` ارث می‌برد، نه `EnrollmentError`. چون خطای کاربر نیست و نباید همراه خطاهای معمول گرفته و نادیده شود.

### نمونهٔ مدیریت خطا
```python
try:
    svc.enroll(StudentId("s1"), CourseId("FM201"))
except PrerequisiteNotMetError as e:
    print("درس‌های کم‌شده:", sorted(e.missing))
except CourseFullError:
    print("ظرفیت پر است")
except EnrollmentError as e:
    print("خطای ثبت‌نام:", e)
```

---

## 8. مرجع کامل API

در همهٔ دستورها، اگر پیش‌شرطی نقض شود، **state هیچ تغییری نمی‌کند** (اتمی‌بودن). این رفتار با تست `test_failed_command_leaves_state_unchanged` بررسی شده است.

### 8.1 سازنده

```python
EnrollmentService(check_invariants: bool = True)
```
اگر `check_invariants=False` باشد، `_verify()` اجرا نمی‌شود (برای کاهش هزینه در محیط تولید).

---

### 8.2 دستورها (Commands)

#### `register_student(student)`
ثبت دانشجوی جدید.

| | |
|---|---|
| **پیش‌شرط** | `student.id ∉ students` |
| **پس‌شرط** | `student.id ∈ students` و `completed(student.id) = ∅` |
| **خطاها** | `DuplicateEntityError` |

#### `register_course(course)`
ثبت درس جدید.

| | |
|---|---|
| **پیش‌شرط** | `course.id ∉ courses` و `course.prerequisites ⊆ courses` |
| **پس‌شرط** | `course.id ∈ courses` و `enrolled(course.id) = ∅` |
| **خطاها** | `DuplicateEntityError`، `UnknownCourseError` (پیش‌نیاز ناشناخته) |

#### `enroll(sid, cid)`
ثبت‌نام دانشجو در درس.

| | |
|---|---|
| **پیش‌شرط‌ها (به‌ترتیب بررسی)** | ۱) درس و دانشجو وجود دارند<br>۲) `sid ∉ enrolled(cid)`<br>۳) `cid ∉ completed(sid)`<br>۴) `prerequisites(cid) ⊆ completed(sid)`<br>۵) `#enrolled(cid) < capacity(cid)` |
| **پس‌شرط** | `sid ∈ enrolled(cid)` و اندازهٔ فهرست دقیقاً یکی زیاد شده |
| **خطاها** | `UnknownCourseError`، `UnknownStudentError`، `AlreadyEnrolledError`، `AlreadyCompletedError`، `PrerequisiteNotMetError`، `CourseFullError` |
| **اثر جانبی** | ثبت `Event(ENROLLED, ...)` |

#### `drop(sid, cid)`
حذف دانشجو از درس بدون گذراندن آن.

| | |
|---|---|
| **پیش‌شرط** | `sid ∈ enrolled(cid)` |
| **پس‌شرط** | `sid ∉ enrolled(cid)` (و `completed` بدون تغییر) |
| **خطاها** | `UnknownCourseError`، `UnknownStudentError`، `NotEnrolledError` |
| **اثر جانبی** | ثبت `Event(DROPPED, ...)` |

#### `complete(sid, cid)`
گذراندن درس. دانشجو از `enrolled(cid)` خارج و به `completed(sid)` اضافه می‌شود.

| | |
|---|---|
| **پیش‌شرط** | `sid ∈ enrolled(cid)` |
| **پس‌شرط** | `sid ∉ enrolled(cid)` و `cid ∈ completed(sid)` |
| **خطاها** | `UnknownCourseError`، `UnknownStudentError`، `NotEnrolledError` |
| **اثر جانبی** | ثبت `Event(COMPLETED, ...)` |

---

### 8.3 کوئری‌ها (Queries)

همهٔ کوئری‌ها **خالص** هستند (بدون تغییر state) و مجموعه‌ها را به‌صورت `frozenset` برمی‌گردانند. نتیجه یک **کپی تغییرناپذیر** است و دستکاری آن روی state سرویس اثری ندارد.

| متد | ورودی | خروجی | تعریف ریاضی |
|---|---|---|---|
| `roster(cid)` | شناسهٔ درس | `frozenset[StudentId]` | `enrolled(cid)` |
| `completed_by(sid)` | شناسهٔ دانشجو | `frozenset[CourseId]` | `completed(sid)` |
| `students_in_either(a, b)` | دو درس | `frozenset[StudentId]` | `enrolled(a) ∪ enrolled(b)` |
| `students_in_both(a, b)` | دو درس | `frozenset[StudentId]` | `enrolled(a) ∩ enrolled(b)` |
| `students_only_in(a, b)` | دو درس | `frozenset[StudentId]` | `enrolled(a) \ enrolled(b)` |
| `students_in_any(cids)` | چند درس | `frozenset[StudentId]` | `⋃ enrolled(cᵢ)` |
| `students_in_all(cids)` | چند درس | `frozenset[StudentId]` | `⋂ enrolled(cᵢ)` (ورودی خالی ⇒ مجموعهٔ خالی) |
| `is_roster_subset(a, b)` | دو درس | `bool` | `enrolled(a) ⊆ enrolled(b)` |
| `are_rosters_disjoint(a, b)` | دو درس | `bool` | `enrolled(a) ∩ enrolled(b) = ∅` |
| `missing_prerequisites(sid, cid)` | دانشجو، درس | `frozenset[CourseId]` | `prerequisites(cid) \ completed(sid)` |
| `can_take(sid, cid)` | دانشجو، درس | `bool` | `prerequisites(cid) ⊆ completed(sid)` |
| `eligible_courses(sid)` | دانشجو | `frozenset[CourseId]` | شرح پایین |

> `can_take` فقط شرط پیش‌نیاز را می‌سنجد. ظرفیت و ثبت‌نام قبلی را بررسی نمی‌کند. برای پاسخ کامل از `eligible_courses` استفاده کنید.

#### `eligible_courses(sid)`
```
{ c ∈ courses |  c ∉ completed(sid)
               ∧ sid ∉ enrolled(c)
               ∧ prerequisites(c) ⊆ completed(sid)
               ∧ #enrolled(c) < capacity(c) }
```

#### خاصیت `audit_log`
```python
svc.audit_log   # tuple[Event, ...]
```
یک **عکس لحظه‌ای تغییرناپذیر** (`tuple`) از لاگ برمی‌گرداند. کسی نمی‌تواند از بیرون لاگ را تغییر دهد.

---

### 8.4 متدهای داخلی

| متد | کار |
|---|---|
| `_student(sid)` | دانشجو را برمی‌گرداند یا `UnknownStudentError` می‌دهد |
| `_course(cid)` | درس را برمی‌گرداند یا `UnknownCourseError` می‌دهد |
| `_verify()` | ناورداهای I1 تا I5 را بررسی می‌کند |

---

## 9. نگاشت عملیات مجموعه‌ای به سناریوهای واقعی

| عملیات | سناریو در دانشگاه | متد |
|---|---|---|
| **اجتماع** | «ساعت کلاس A یا B تغییر کرد. به چه کسانی اطلاع بدهیم؟» | `students_in_either` |
| **اشتراک** | «چه کسانی هر دو درس را دارند؟ احتمال تداخل امتحان» | `students_in_both` |
| **تفاضل** | «اگر فقط کلاس A لغو شود، چه کسانی آسیب می‌بینند؟» | `students_only_in` |
| **تفاضل** | «این دانشجو کدام پیش‌نیازها را کم دارد؟» | `missing_prerequisites` |
| **زیرمجموعه** | «آیا همهٔ پیش‌نیازها گذرانده شده؟» | `can_take` |
| **زیرمجموعه** | «آیا کلاس A کاملاً داخل کلاس B است؟ می‌توان ادغام کرد؟» | `is_roster_subset` |
| **مجزا بودن** | «آیا دو کلاس هیچ دانشجوی مشترکی ندارند؟ می‌توان همزمان برگزار کرد» | `are_rosters_disjoint` |
| **اجتماع تعمیم‌یافته** | «همهٔ دانشجویان گروه آموزشی نرم‌افزار» | `students_in_any` |
| **اشتراک تعمیم‌یافته** | «دانشجویانی که هر سه درس را دارند» | `students_in_all` |
| **تعریف با شرط** | «این دانشجو الان چه درس‌هایی می‌تواند بردارد؟» | `eligible_courses` |

---

## 10. تصمیم‌های طراحی

### ۱. اشیای ارزشی تغییرناپذیر (`frozen=True`)
- **دلیل:** برای قرار گرفتن داخل مجموعه‌ها باید hashable باشند و تغییرناپذیری جلوی خطاهای ناشی از تغییر پنهان را می‌گیرد.
- **هزینه:** تغییر یک مقدار نیازمند ساخت شیء جدید است که برای این دامنه مشکلی ندارد.

### ۲. بازگرداندن `frozenset` از کوئری‌ها
- **دلیل:** اگر `set` داخلی برگردانده می‌شد، فراخواننده می‌توانست state را بدون عبور از قواعد تغییر دهد و ناورداها شکسته می‌شد (نشت encapsulation).

### ۳. تنها نقطهٔ تغییر: `EnrollmentService`
- **دلیل:** همهٔ قواعد در یک جا اعمال می‌شوند و راه دور زدن آن‌ها وجود ندارد.

### ۴. خطای اختصاصی برای هر پیش‌شرط
- **دلیل:** فراخواننده می‌تواند هر خطا را متفاوت مدیریت کند (مثلاً نمایش پیام مناسب به کاربر). `PrerequisiteNotMetError` حتی دلیل دقیق را همراه دارد.

### ۵. تفکیک خطای کاربر از باگ
- خطاهای `EnrollmentError` یعنی «درخواست نامعتبر بود».
- `InvariantViolation` یعنی «برنامه‌نویس اشتباه کرده». این دو عمداً از دو شاخهٔ متفاوت ارث می‌برند.

### ۶. بررسی ناورداها بعد از هر دستور
- **مزیت:** باگ‌ها بلافاصله و نزدیک محل وقوع شناسایی می‌شوند.
- **هزینه:** `_verify()` روی همهٔ درس‌ها و دانشجوهای ثبت‌نام‌شده حلقه می‌زند. با `check_invariants=False` قابل خاموش شدن است.

### ۷. `assert` برای پس‌شرط‌ها
- پس‌شرط‌ها ادعاهای داخلی دربارهٔ درستی خود کد هستند، نه اعتبارسنجی ورودی. به همین دلیل با `assert` نوشته شده‌اند. توجه کنید با اجرای پایتون در حالت `-O` حذف می‌شوند.

### ۸. لاگ فقط‌افزودنی (Audit Log)
- امکان ردیابی تاریخچه و بازسازی state را فراهم می‌کند و پایهٔ مناسبی برای الگوی Event Sourcing است.

---

## 11. تست‌ها

فایل `test_enrollment_system.py` با `unittest` نوشته شده و **۱۷ تست** در سه کلاس دارد. هر تست از نمونهٔ دمو (`build_demo()`) شروع می‌کند.

### کلاس `EnrollmentRules` (۱۰ تست): قواعد کسب‌وکار

| تست | چه چیزی را بررسی می‌کند |
|---|---|
| `test_enroll_adds_to_roster` | ثبت‌نام، دانشجو را به فهرست اضافه می‌کند |
| `test_duplicate_enrollment_rejected` | ثبت‌نام تکراری رد می‌شود |
| `test_prerequisite_enforced_and_reports_missing_set` | پیش‌نیاز اعمال می‌شود و `missing` دقیق است |
| `test_capacity_enforced` | ثبت‌نام در درس پر رد می‌شود |
| `test_complete_moves_student_between_sets` | `complete` دانشجو را از یک مجموعه به مجموعهٔ دیگر منتقل می‌کند |
| `test_drop_requires_enrollment` | `drop` بدون ثبت‌نام قبلی خطا می‌دهد |
| `test_unknown_entities` | دانشجو یا درس ناشناخته خطا می‌دهد |
| `test_failed_command_leaves_state_unchanged` | دستور ناموفق state را تغییر نمی‌دهد |
| `test_audit_log_is_append_only_snapshot` | لاگ با هر دستور موفق رشد می‌کند |
| `test_queries_return_immutable_sets` | کوئری‌ها `frozenset` برمی‌گردانند |

### کلاس `SetQueries` (۵ تست): کوئری‌های مجموعه‌ای

| تست | چه چیزی را بررسی می‌کند |
|---|---|
| `test_union_intersection_difference` | نتایج اجتماع، اشتراک و تفاضل روی داده‌های دمو |
| `test_subset_and_disjoint` | زیرمجموعه بودن و مجزا بودن |
| `test_generalised_operations` | اجتماع و اشتراک تعمیم‌یافته، از جمله ورودی خالی |
| `test_eligibility` | `can_take` و `eligible_courses` بعد از گذراندن پیش‌نیازها |
| `test_set_laws_hold_for_every_pair_of_courses` | قوانین جبر مجموعه‌ها روی همهٔ جفت درس‌ها |

**قوانینی که در تست آخر چک می‌شوند:**
- جابه‌جایی: `A ∪ B = B ∪ A` و `A ∩ B = B ∩ A`
- اصل شمول و عدم شمول: `|A ∪ B| = |A| + |B| − |A ∩ B|`
- افراز: `(A \ B) ∪ (A ∩ B) = A`
- مجزا بودن: `(A \ B) ∩ (A ∩ B) = ∅`

### کلاس `Invariants` (۲ تست)

| تست | چه چیزی را بررسی می‌کند |
|---|---|
| `test_tampering_is_detected` | با دستکاری مستقیم state (شبیه‌سازی باگ)، `_verify()` خطا می‌دهد |
| `test_value_object_validation` | `Course` با ظرفیت صفر یا پیش‌نیاز خودش ساخته نمی‌شود |

### نکتهٔ روش‌شناختی
تست‌ها فقط **نمونه‌هایی** را می‌سنجند و اثبات صوری نیستند. اما ناورداهای داخل کد اصلی در زمان اجرا روی **همهٔ حالت‌های رسیده‌شده** بررسی می‌شوند. ترکیب این دو، شواهد قوی (نه اثبات کامل) بر درستی پیاده‌سازی است.

---

## 12. اجرای نمونه (Demo)

### داده‌های اولیه (`build_demo`)

- **دانشجویان:** `s1` (Ali)، `s2` (Sara)، `s3` (Reza)، `s4` (Mina)
- **درس‌ها:**
  - `CS101` (ظرفیت ۳)
  - `MATH101` (ظرفیت ۳)
  - `FM201` (ظرفیت ۲، پیش‌نیاز: `CS101` و `MATH101`)
- **ثبت‌نام‌ها:** `CS101 ← {s1, s2, s3}` و `MATH101 ← {s2, s3, s4}`

### خروجی `python enrollment_system.py`
```
Union        : ['s1', 's2', 's3', 's4']
Intersection : ['s2', 's3']
Difference   : ['s1']
Disjoint?    : False
s2 can take FM201: True
s1 missing       : ['CS101', 'MATH101']
s2 eligible      : ['FM201']
Rejected: s1 cannot take FM201; missing: ['CS101', 'MATH101']
Audit log size   : 10
```

### توضیح خروجی

| خط | توضیح |
|---|---|
| Union | `{s1,s2,s3} ∪ {s2,s3,s4}` |
| Intersection | `{s1,s2,s3} ∩ {s2,s3,s4} = {s2,s3}` |
| Difference | `{s1,s2,s3} \ {s2,s3,s4} = {s1}` |
| Disjoint? | اشتراک خالی نیست پس `False` |
| s2 can take FM201 | `s2` و `s3` هر دو پیش‌نیاز را با `complete` گذرانده‌اند و `{CS101, MATH101} ⊆ completed(s2)` |
| s1 missing | `s1` هنوز هیچ درسی نگذرانده است |
| Rejected | ثبت‌نام `s1` در `FM201` با `PrerequisiteNotMetError` رد می‌شود |
| Audit log size | ۶ ثبت‌نام اولیه + ۴ اتمام درس = ۱۰ رویداد |

---

## 13. محدودیت‌ها

- **فقط در حافظه:** با بسته شدن برنامه همه‌چیز از بین می‌رود و ذخیره‌سازی ماندگار (دیتابیس) وجود ندارد.
- **غیرایمن در برابر چند نخ (not thread-safe):** برای استفادهٔ همزمان باید قفل اضافه شود.
- **هزینهٔ `_verify()`:** روی هر دستور کل سیستم را بررسی می‌کند، پس با رشد داده کند می‌شود (در حال حاضر خطی نسبت به تعداد ثبت‌نام‌ها).
- **مدل ساده از «گذراندن»:** نمره، ترم و مردود شدن مدل نشده‌اند و `complete` یعنی قبول شدن قطعی.
- **بدون بازگشت از `complete`:** عملیاتی برای لغو گذراندن درس وجود ندارد و این عمداً برای حفظ I5 است.
- **عدم تکرار درس:** دانشجو نمی‌تواند درس گذرانده‌شده را دوباره بردارد.
- **پس‌شرط‌ها با `assert`:** در حالت بهینه‌شدهٔ پایتون (`python -O`) اجرا نمی‌شوند.
- **اثبات صوری وجود ندارد:** درستی با تست و بررسی زمان اجرا نشان داده می‌شود، نه با اثبات ریاضی.

---

## 14. راه‌های توسعه

| ایده | توضیح |
|---|---|
| **تست مبتنی بر ویژگی (Property-based)** | استفاده از `hypothesis` برای تولید خودکار سناریوهای تصادفی و بررسی ناورداها |
| **لیست انتظار** | مجموعهٔ `waitlist(c)` و انتقال خودکار با آزاد شدن ظرفیت |
| **هم‌نیاز (Co-requisite)** | درس‌هایی که باید همزمان گرفته شوند (`corequisites(c) ⊆ completed(s) ∪ enrolled-now(s)`) |
| **سقف واحد ترم** | محدودیت بر مجموع واحدهای ثبت‌نام‌شده |
| **ذخیره‌سازی** | افزودن لایهٔ Repository برای ذخیره در SQLite یا فایل |
| **بازسازی از لاگ** | ساخت state از روی `audit_log` (Event Sourcing) |
| **مشخصات صوری رسمی** | بازنویسی مدل با Alloy، Z یا TLA+ و تطبیق با پیاده‌سازی |
| **بررسی نوع ایستا** | اجرای `mypy --strict` روی کد |

---

## 15. واژه‌نامه

| اصطلاح | توضیح |
|---|---|
| **State (حالت)** | مجموعهٔ مقادیر داده‌های سیستم در یک لحظه |
| **Invariant (ناوردا)** | شرطی که در همهٔ حالت‌های قابل‌دسترس باید برقرار باشد |
| **Precondition (پیش‌شرط)** | شرطی که قبل از اجرای عملیات باید برقرار باشد |
| **Postcondition (پس‌شرط)** | شرطی که بعد از اجرای عملیات باید برقرار باشد |
| **Design by Contract** | طراحی بر پایهٔ قرارداد پیش‌شرط/پس‌شرط/ناوردا |
| **Value Object** | شیء تغییرناپذیر که با مقدارش شناخته می‌شود |
| **Aggregate Root** | شیئی که تنها نقطهٔ ورود برای تغییر مجموعه‌ای از اشیای مرتبط است |
| **CQS** | جداسازی دستورهای تغییردهنده از کوئری‌های فقط‌خواندنی |
| **Frozenset** | مجموعهٔ تغییرناپذیر و hashable در پایتون |
| **DAG** | گراف جهت‌دار بدون دور |
| **Audit Log** | ثبت فقط‌افزودنی رویدادهای سیستم |
| **Event Sourcing** | ذخیرهٔ state به‌صورت دنبالهٔ رویدادها |
| **Z / B Method** | زبان‌ها و روش‌های مشخصات صوری مبتنی بر نظریهٔ مجموعه‌ها |