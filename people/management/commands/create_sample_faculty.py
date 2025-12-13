from django.core.management.base import BaseCommand
from people.models import BaseUser, Faculty, AllowedEmail
from django.contrib.auth.hashers import make_password
from datetime import date


class Command(BaseCommand):
    help = 'Create sample faculty members with different designations and roles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-specific',
            action='store_true',
            help='Create only Dr. Shah Murtaza Rashid Al Masud and Mahedi Hasan',
        )
        parser.add_argument(
            '--create-former',
            action='store_true',
            help='Create 3 former faculty members with last_office_date set',
        )

    def handle(self, *args, **options):
        create_specific = options.get('create_specific', False)
        create_former = options.get('create_former', False)
        
        if create_former:
            # Create 3 former faculty members
            former_faculty_data = [
                {
                    'name': 'Dr. Mohammad Ali',
                    'email': 'mohammad.ali@uap-cse.edu',
                    'designation': 'Professor',
                    'shortname': 'MA',
                    'phone': '01712345692',
                    'bio': 'Former Professor specializing in Artificial Intelligence and Machine Learning',
                    'is_head': False,
                    'is_dept_proctor': False,
                    'is_bsc_admission_coordinator': False,
                    'is_mcse_admission_coordinator': False,
                    'is_on_study_leave': False,
                    'last_office_date': date(2023, 12, 31),
                    'sl': 10,
                },
                {
                    'name': 'Dr. Fatima Begum',
                    'email': 'fatima.begum@uap-cse.edu',
                    'designation': 'Associate Professor',
                    'shortname': 'FB',
                    'phone': '01712345693',
                    'bio': 'Former Associate Professor with expertise in Database Systems and Data Mining',
                    'is_head': False,
                    'is_dept_proctor': False,
                    'is_bsc_admission_coordinator': False,
                    'is_mcse_admission_coordinator': False,
                    'is_on_study_leave': False,
                    'last_office_date': date(2024, 6, 30),
                    'sl': 11,
                },
                {
                    'name': 'Dr. Hasan Mahmud',
                    'email': 'hasan.mahmud@uap-cse.edu',
                    'designation': 'Assistant Professor',
                    'shortname': 'HM',
                    'phone': '01712345694',
                    'bio': 'Former Assistant Professor specializing in Software Engineering and Web Technologies',
                    'is_head': False,
                    'is_dept_proctor': False,
                    'is_bsc_admission_coordinator': False,
                    'is_mcse_admission_coordinator': False,
                    'is_on_study_leave': False,
                    'last_office_date': date(2024, 11, 30),
                    'sl': 12,
                },
            ]
            self.create_faculty_members(former_faculty_data)
            return
        
        if create_specific:
            # Create only the two specific faculty members
            specific_faculty_data = [
                {
                    'name': 'Dr. Shah Murtaza Rashid Al Masud',
                    'email': 'shah.murtaza@uap-cse.edu',
                    'designation': 'Professor',
                    'shortname': 'SMRAM',
                    'phone': '01712345690',
                    'bio': 'Head of Department with extensive research experience',
                    'is_head': True,
                    'is_dept_proctor': False,
                    'is_bsc_admission_coordinator': False,
                    'is_mcse_admission_coordinator': False,
                    'is_on_study_leave': False,
                    'sl': 1,
                },
                {
                    'name': 'Mahedi Hasan',
                    'email': 'mahedi.hasan@uap-cse.edu',
                    'designation': 'Lecturer',
                    'shortname': 'MH',
                    'phone': '01712345691',
                    'bio': 'Lecturer currently on study leave',
                    'is_head': False,
                    'is_dept_proctor': False,
                    'is_bsc_admission_coordinator': False,
                    'is_mcse_admission_coordinator': False,
                    'is_on_study_leave': True,
                    'sl': 2,
                },
            ]
            self.create_faculty_members(specific_faculty_data)
            return
        
        # Sample faculty data
        faculty_data = [
            {
                'name': 'Dr. Ahmed Rahman',
                'email': 'ahmed.rahman@uap-cse.edu',
                'designation': 'Professor',
                'shortname': 'AR',
                'phone': '01712345678',
                'bio': 'Head of Department with expertise in Machine Learning and AI',
                'is_head': True,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 1,
            },
            {
                'name': 'Dr. Fatima Khan',
                'email': 'fatima.khan@uap-cse.edu',
                'designation': 'Associate Professor',
                'shortname': 'FK',
                'phone': '01712345679',
                'bio': 'BSc Admission Coordinator specializing in Database Systems',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': True,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 2,
            },
            {
                'name': 'Dr. Mohammad Hassan',
                'email': 'mohammad.hassan@uap-cse.edu',
                'designation': 'Associate Professor',
                'shortname': 'MH',
                'phone': '01712345680',
                'bio': 'MCSE Admission Coordinator with research in Cloud Computing',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': True,
                'is_on_study_leave': False,
                'sl': 3,
            },
            {
                'name': 'Dr. Ayesha Ali',
                'email': 'ayesha.ali@uap-cse.edu',
                'designation': 'Assistant Professor',
                'shortname': 'AA',
                'phone': '01712345681',
                'bio': 'Department Proctor and expert in Software Engineering',
                'is_head': False,
                'is_dept_proctor': True,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 4,
            },
            {
                'name': 'Dr. Karim Uddin',
                'email': 'karim.uddin@uap-cse.edu',
                'designation': 'Assistant Professor',
                'shortname': 'KU',
                'phone': '01712345682',
                'bio': 'Specialist in Computer Networks and Cybersecurity',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 5,
            },
            {
                'name': 'Dr. Nusrat Jahan',
                'email': 'nusrat.jahan@uap-cse.edu',
                'designation': 'Lecturer',
                'shortname': 'NJ',
                'phone': '01712345683',
                'bio': 'Expert in Web Development and Mobile Applications',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 6,
            },
            {
                'name': 'Dr. Rashed Islam',
                'email': 'rashed.islam@uap-cse.edu',
                'designation': 'Lecturer',
                'shortname': 'RI',
                'phone': '01712345684',
                'bio': 'Specializing in Data Structures and Algorithms',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 7,
            },
            {
                'name': 'Dr. Tahmina Begum',
                'email': 'tahmina.begum@uap-cse.edu',
                'designation': 'Teaching Assistant',
                'shortname': 'TB',
                'phone': '01712345685',
                'bio': 'Graduate Teaching Assistant in Programming Fundamentals',
                'is_head': False,
                'is_dept_proctor': False,
                'is_bsc_admission_coordinator': False,
                'is_mcse_admission_coordinator': False,
                'is_on_study_leave': False,
                'sl': 8,
            },
        ]
        
        self.create_faculty_members(faculty_data)
    
    def create_faculty_members(self, faculty_data):
        created_count = 0
        skipped_count = 0

        for data in faculty_data:
            email = data['email']

            # Check if user already exists
            if BaseUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Skipping {data['name']} - user with email {email} already exists")
                )
                skipped_count += 1
                continue

            try:
                # Create AllowedEmail first
                allowed_email = AllowedEmail.objects.create(
                    email=email,
                    user_type='faculty',
                    is_power_user=False,
                    is_active=True,
                    is_blocked=False,
                )

                # Create BaseUser
                name_parts = data['name'].split()
                base_user = BaseUser.objects.create(
                    username=email.split('@')[0],
                    email=email,
                    first_name=name_parts[0] if len(name_parts) > 0 else data['name'],
                    last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
                    password=make_password('faculty123'),  # Default password
                    user_type='faculty',
                    allowed_email=allowed_email,
                    is_power_user=False,
                )

                # Create Faculty profile
                faculty = Faculty.objects.create(
                    base_user=base_user,
                    name=data['name'],
                    shortname=data['shortname'],
                    designation=data['designation'],
                    phone=data['phone'],
                    bio=data['bio'],
                    is_head=data['is_head'],
                    is_dept_proctor=data['is_dept_proctor'],
                    is_bsc_admission_coordinator=data['is_bsc_admission_coordinator'],
                    is_mcse_admission_coordinator=data['is_mcse_admission_coordinator'],
                    is_on_study_leave=data.get('is_on_study_leave', False),
                    last_office_date=data.get('last_office_date', None),
                    sl=data['sl'],
                    joining_date=date(2020, 1, 1),  # Default joining date
                )

                role_info = []
                if faculty.is_head:
                    role_info.append("Head of Department")
                if faculty.is_dept_proctor:
                    role_info.append("Department Proctor")
                if faculty.is_bsc_admission_coordinator:
                    role_info.append("BSc Admission Coordinator")
                if faculty.is_mcse_admission_coordinator:
                    role_info.append("MCSE Admission Coordinator")
                if faculty.is_on_study_leave:
                    role_info.append("On Study Leave")
                if faculty.last_office_date:
                    role_info.append(f"Former (Until {faculty.last_office_date.strftime('%B %Y')})")

                role_str = f" ({', '.join(role_info)})" if role_info else ""

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {faculty.name} - {faculty.designation}{role_str}")
                )
                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating {data['name']}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n📊 Summary: {created_count} created, {skipped_count} skipped")
        )
