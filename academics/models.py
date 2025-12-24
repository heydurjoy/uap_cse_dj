from django.db import models
from django.conf import settings


# ==============================================================================
# I. FIXED CHOICE DEFINITIONS (KPA, BLOOMS, COURSE TYPE)
# ==============================================================================

# Course Type Choices
COURSE_TYPE_CHOICES = (
    ('TH', 'Theory'),
    ('LB', 'Lab'),
)

# Year-Semester Choices
YEAR_SEMESTER_CHOICES = (
    ('1-1', 'Year 1, Semester 1'),
    ('1-2', 'Year 1, Semester 2'),
    ('2-1', 'Year 2, Semester 1'),
    ('2-2', 'Year 2, Semester 2'),
    ('3-1', 'Year 3, Semester 1'),
    ('3-2', 'Year 3, Semester 2'),
    ('4-1', 'Year 4, Semester 1'),
    ('4-2', 'Year 4, Semester 2'),
)

# Bloom's Taxonomy across domains
BLOOMS_CHOICES = (
    # Cognitive Domain (Knowledge – K1 to K6)
    ('K1', 'K1: Remember – Recall facts and basic concepts'),
    ('K2', 'K2: Understand – Explain ideas or concepts'),
    ('K3', 'K3: Apply – Use information in new situations'),
    ('K4', 'K4: Analyze – Break information into parts / Compare'),
    ('K5', 'K5: Evaluate – Justify decisions / Judge value'),
    ('K6', 'K6: Create – Produce new or original work'),

    # Affective Domain (Attitudes – A1 to A5)
    ('A1', 'A1: Receiving – Awareness / Willingness to listen'),
    ('A2', 'A2: Responding – Participation / Active engagement'),
    ('A3', 'A3: Valuing – Acceptance of values / Commitment'),
    ('A4', 'A4: Organizing – Integrating values / Prioritizing'),
    ('A5', 'A5: Characterizing – Consistent value-driven behavior'),

    # Psychomotor Domain (Skills – P1 to P5)
    ('P1', 'P1: Imitation – Copying actions / Following demonstration'),
    ('P2', 'P2: Manipulation – Performing with guidance'),
    ('P3', 'P3: Precision – Accurate, independent performance'),
    ('P4', 'P4: Articulation – Coordinated, combined skills'),
    ('P5', 'P5: Naturalization – Automatic, mastery-level performance'),
)

# Knowledge Profile (KP) Choices
KP_CHOICES = (
    ('K1', 'K1: Systematic Natural Sciences (Physics, Chemistry, Biology)'),
    ('K2', 'K2: Conceptually Based Math/Stats (Analytical tools and models)'),
    ('K3', 'K3: Theory-Based Engineering Fmntls (Core engineering principles)'),
    ('K4', 'K4: Specialist Knowledge/Forefront (Advanced, niche discipline knowledge)'),
    ('K5', 'K5: Engineering Design Support (Knowledge for creating solutions)'),
    ('K6', 'K6: Engineering Practice (Technology) (Application of techniques/tools)'),
    ('K7', 'K7: Role in Society & Ethics (Impacts, responsibility, safety)'),
    ('K8', 'K8: Research Literature Engagement (Using published academic research)'),
)

# Problem Attribute (P) Choices
PA_CHOICES = (
    ('P1', 'P1: In-Depth Knowledge Required (Needs K1-K8 level knowledge)'),
    ('P2', 'P2: Wide-Ranging/Conflicting Req. (Involves multiple disciplines/issues)'),
    ('P3', 'P3: No Obvious Solution/Abstract (Requires originality and modeling)'),
    ('P4', 'P4: Infrequently Encountered Issues (Problems outside routine experience)'),
    ('P5', 'P5: Outside Standards/Codes (Solution goes beyond standard practices)'),
    ('P6', 'P6: Diverse Stakeholder Needs (Many groups with varying, complex needs)'),
    ('P7', 'P7: Many Interdependent Parts (High-level system with sub-problems)'),
)

# Activity Attribute (A) Choices
A_CHOICES = (
    ('A1', 'A1: Diverse Resource Use (Involves people, money, equipment, etc.)'),
    ('A2', 'A2: Resolve Significant Conflicts (Managing wide-ranging/conflicting issues)'),
    ('A3', 'A3: Creative Use of Principles (Applying novel or unconventional methods)'),
    ('A4', 'A4: Significant Consequences (High risk/difficulty in prediction)'),
    ('A5', 'A5: Beyond Previous Experience (Applying principles-based, non-routine approaches)'),
)

# ------------------------------------------------------------------------------

## 1. Program Model
class Program(models.Model):
    """Defines a degree program (e.g., BSc in CSE, MSc in EE)."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Degree Program Name")
    
    class Meta:
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'
        ordering = ['name']
    
    def __str__(self):
        return self.name


## 2. Program Learning Outcome (PLO) Model
class ProgramOutcome(models.Model):
    """High-level goals achieved by students upon graduation."""
    code = models.CharField(max_length=10, unique=True, help_text="e.g., PLO1, PLO2, PLO3")
    title = models.CharField(max_length=255)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='program_outcomes')
    description = models.TextField(blank=True, help_text="The full statement for the Program Learning Outcome.")
    
    class Meta:
        verbose_name = 'Program Learning Outcome'
        verbose_name_plural = 'Program Learning Outcomes'
        ordering = ['program', 'code']
        unique_together = ['code', 'program']
    
    def __str__(self):
        return f"{self.code} ({self.program.name})"


## 3. Course Model
class Course(models.Model):
    """Defines a specific course offering, including type and official outline."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20, unique=True, help_text="e.g., CSE 2101")
    title = models.CharField(max_length=255)
    credit_hours = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="Credit Hours (Cr Hr)")
    contact_hours = models.PositiveSmallIntegerField(verbose_name="Contact Hours") 
    
    course_type = models.CharField(
        max_length=2,
        choices=COURSE_TYPE_CHOICES,
        default='TH',
        verbose_name="Course Type",
        help_text="Designates if the course is Theory (TH) or Lab (LB)."
    )
    
    year_semester = models.CharField(
        max_length=3,
        choices=YEAR_SEMESTER_CHOICES,
        default='1-1',
        verbose_name="Year-Semester",
        help_text="The academic year and semester when this course is offered (e.g., 1-1, 2-2)."
    )
    
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='required_for',
        verbose_name="Prerequisite Courses",
        help_text="Select courses that must be completed before taking this course."
    )
    
    # Field for PDF Course Outline
    course_outline_pdf = models.FileField(
        upload_to='course_outlines/', 
        null=True, 
        blank=True,
        verbose_name="Course Outline PDF",
        help_text="Upload the official PDF document containing the course outline/syllabus (Max 5MB)."
    )
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['program', 'year_semester', 'course_code']
    
    def __str__(self):
        return f"[{self.course_type}] {self.course_code} - {self.title}"


## 4. Course Learning Outcome (CLO) and Mapping Model
class CourseOutcome(models.Model):
    """Defines what a student should be able to do at the end of a course, 
       and maps it to a single Program Learning Outcome and fixed KPA attributes."""
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='outcomes')
    
    # Sequence number replaces the CharField code for sorting and uniqueness per course
    sequence_number = models.PositiveSmallIntegerField(
        help_text="The unique sequence number (1, 2, 3...) for this CLO within the course.",
        verbose_name="CLO Sequence Number"
    )
    
    statement = models.TextField(verbose_name="Course Learning Outcome Statement") 

    # CO to PO Mapping (One-to-One)
    program_outcome = models.ForeignKey(
        ProgramOutcome,
        on_delete=models.RESTRICT, 
        related_name='contributing_outcomes',
        verbose_name="Mapped Program Learning Outcome",
        help_text="A Course Learning Outcome must map to exactly one Program Learning Outcome."
    )
    
    # Detailed Attributes from Fixed Choices
    blooms_level = models.CharField(max_length=10, choices=BLOOMS_CHOICES, help_text="The cognitive level being assessed.")
    knowledge_profile = models.CharField(max_length=10, choices=KP_CHOICES, help_text="Select the primary knowledge type addressed.")
    problem_attribute = models.CharField(max_length=10, choices=PA_CHOICES, help_text="Select the attribute that best defines the problem complexity.")
    activity_attribute = models.CharField(max_length=10, choices=A_CHOICES, blank=True, null=True, help_text="Select the characteristic that defines the required engineering activity.")

    # Assessment and Activity Data
    total_assessment_marks = models.PositiveSmallIntegerField(
        default=0, 
        help_text="Total marks across all assessments used to measure this specific CO."
    )
    activity = models.CharField(
        max_length=100, 
        help_text="The primary pedagogical activity type (e.g., Lecture, Laboratory Session, Design Project)."
    )

    class Meta:
        verbose_name = 'Course Learning Outcome'
        verbose_name_plural = 'Course Learning Outcomes'
        # Enforce that the sequence_number must be unique FOR EACH course
        unique_together = ('course', 'sequence_number')
        ordering = ['course', 'sequence_number']

    def __str__(self):
        return f"{self.course.course_code} - CLO{self.sequence_number}"
