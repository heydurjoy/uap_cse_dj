from django.core.management.base import BaseCommand
from people.models import Contributor
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate Contributor model with initial data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing contributors before populating',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            Contributor.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing contributors'))
        
        # Final Development & Deployment contributors
        final_contributors = [
            {
                'name': 'Durjoy Mistry',
                'student_id': None,
                'role': 'Concept, system architecture, major development, technical supervision, integration, and final approval',
                'reflection': None,
                'portfolio_link': None,
                'image': 'images/profile-durjoy-mistry.jpg',  # You'll need to add this image
                'project_type': 'final',
                'order': 1,
            },
            {
                'name': 'Tahiya Zareen Hiya',
                'student_id': '22201038',
                'role': 'Final implementation, feature completion, testing, optimization, and deployment',
                'reflection': 'I feel really excited and honored to be part of this journey. I\'m really thankful to Durjoy Mistry sir, the Mastermind of this website for giving me this great opportunity to apply my skills  while also learning how to integrate user-friendly features and maintain a consistent design system.',
                'portfolio_link': 'https://tahiya07.github.io/Tahiya.view/',
                'image': 'images/profile - Tahiya Zareen.jpg',
                'project_type': 'final',
                'order': 2,
            },
        ]
        
        # Course-Based Development contributors
        course_contributors = [
            {
                'name': 'Durjoy Mistry',
                'student_id': None,
                'role': 'Course teacher, concept exploration, early implementations',
                'reflection': None,
                'portfolio_link': None,
                'image': 'images/profile-durjoy-mistry.jpg',  # You'll need to add this image
                'project_type': 'course',
                'order': 1,
            },
            {
                'name': 'Junaid Hossain',
                'student_id': '22201017',
                'role': 'Backend development for the Club section',
                'reflection': 'Felt good to work on a project that will be used by so many people in the future.',
                'portfolio_link': 'https://junhossain.github.io/Portfolio/',
                'image': 'images/profile-junaid-hossain.jpg',
                'project_type': 'course',
                'order': 2,
            },
            {
                'name': 'Wasikul Hasan Fahim',
                'student_id': '22201037',
                'role': 'Alumni section development',
                'reflection': 'Great to be part of this project',
                'portfolio_link': 'https://wasikul-fahim.github.io/Wasikul_Portfolio/index.html',
                'image': 'images/IMG_3194 - Wasikul Hasan Fahim.jpeg',
                'project_type': 'course',
                'order': 3,
            },
            {
                'name': 'Yeamin Bhuiyan',
                'student_id': '22201056',
                'role': 'Some role here',  # fill in the actual role
                'reflection': 'Reflection goes here',  # fill in the reflection
                'portfolio_link': None,
                'image': 'images/profile-yeamin-bhuiyan.jpg',
                'project_type': 'course',
                'order': 4,
            },
            {
                'name': 'Lubaba Hasan',
                'student_id': '22201057',
                'role': 'Some role here',
                'reflection': 'Reflection goes here',
                'portfolio_link': None,
                'image': 'images/profile-lubaba-hasan.jpg',
                'project_type': 'course',
                'order': 5,
            },
            {
                'name': 'Tasnia Sami',
                'student_id': '22201058',
                'role': 'Some role here',
                'reflection': 'Reflection goes here',
                'portfolio_link': None,
                'image': 'images/profile-tasnia-sami.jpg',
                'project_type': 'course',
                'order': 6,
            },
            {
                'name': 'Ibrahim Hasan',
                'student_id': '22201142',
                'role': 'Academic area, role-based access control, dynamic facts & figures',
                'reflection': 'This journey has played an important role in my learning and growth. I gained valuable knowledge, improved my skills, and built confidence through hands-on experience.',
                'portfolio_link': 'https://drive.google.com/open?id=1ZaC1psjiu1wozN3oS3kPMdEdC0Ebs-LK',
                'image': 'images/IMG_3970 - Ibrahim Hasan.jpeg',
                'project_type': 'course',
                'order': 7,
            },
            {
                'name': 'Fabia Tasnim',
                'student_id': '22201044',
                'role': 'Fullstack (Frontend & Backend) of Alumni Association module, PDF upload & preview, download mechanism',
                'reflection': 'Being part of this journey has been truly rewarding. Special thanks to our mentor Durjoy Mistry for continuous guidance and support.',
                'portfolio_link': 'https://drive.google.com/open?id=1U6v1_kXJYgjcUPtMnHF4vb-93ntVUvIg',
                'image': 'images/IMG-20250101-WA0012 - Fabia Tasnim.jpg',
                'project_type': 'course',
                'order': 8,
            },
            {
                'name': 'Md Sahriar Asif',
                'student_id': '22201111',
                'role': 'Backend developer for Faculty module (password reset, Google Scholar API integration, profile updates)',
                'reflection': 'Learned a bunch of new stuff along the way. Low-key a pretty cool experience.',
                'portfolio_link': 'https://md-sahriar-asif.github.io/Portfolio/',
                'image': 'images/20231220_154235 - Md. Sahriar Asif.jpg',
                'project_type': 'course',
                'order': 9,
            },
            {
                'name': 'Taj Mohammad Anim',
                'student_id': '22201036',
                'role': 'Implementing Chatbot',
                'reflection': 'Building a university website is already a big project—and my role in creating the chatbot is a very important one. It\'s a learning journey, and I\'m genuinely glad to be a part of it.',
                'portfolio_link': 'https://anim36.github.io/My-PORTFOLIO1/',
                'image': 'images/Anim (2) - Taj Mohammad Anim.jpg',
                'project_type': 'course',
                'order': 10,
            },
            {
                'name': 'Rabea Sultana Shazia',
                'student_id': '22201053',
                'role': 'Alumni section',
                'reflection': 'Great experience.I\'m honoured to be a part of this making thanks to Durjoy Mistry sir for the opportunity.',
                'portfolio_link': 'https://drive.google.com/open?id=1NoTIgSNaiOr4nfO-l29HwO3TumSq0ARa',
                'image': 'images/inbound3834883613428923307 - Rabea Sultana Shazia.jpg',
                'project_type': 'course',
                'order': 11,
            },
            {
                'name': 'Marzan Ahmed',
                'student_id': '22201055',
                'role': 'Clubs',
                'reflection': 'It felt great to contribute to a real departmental website & collaborate with the whole team. I learned a lot throughout the process & it was rewarding to see our work come together into something useful for our department. I am always grateful for this opportunity.',
                'portfolio_link': 'https://marzzzsiam.github.io/Marzan_Ahmed/',
                'image': 'images/IMG_7460 - Marzan Ahmed.jpeg',
                'project_type': 'course',
                'order': 12,
            },
            {
                'name': 'Md. Akif Hossain',
                'student_id': '22201029',
                'role': 'Backend Development for Alumni Stories section',
                'reflection': 'I feel honored to have been a part of this journey, as it allowed me to contribute meaningfully to the department while enhancing my technical skills.',
                'portfolio_link': 'https://drive.google.com/open?id=1--GDaF2sS7Cfask7C6cgdd5AZQ5UgdEw',
                'image': 'images/WhatsApp Image 2023-09-14 at 21.10.50 - Md. Akif Hossain.jpg',
                'project_type': 'course',
                'order': 13,
            },
        ]
        
        all_contributors = final_contributors + course_contributors
        created_count = 0
        skipped_count = 0
        
        for data in all_contributors:
            # Check if contributor already exists (by name and project_type)
            if Contributor.objects.filter(name=data['name'], project_type=data['project_type']).exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Skipping {data['name']} ({data['project_type']}) - already exists")
                )
                skipped_count += 1
                continue
            
            try:
                # Create contributor
                contributor = Contributor.objects.create(
                    name=data['name'],
                    student_id=data['student_id'],
                    role=data['role'],
                    reflection=data['reflection'],
                    portfolio_link=data['portfolio_link'] if data['portfolio_link'] else None,
                    project_type=data['project_type'],
                    order=data['order'],
                )
                
                # Try to copy photo from static files if it exists
                image_path = data.get('image')
                if image_path:
                    # Try multiple possible locations
                    possible_paths = [
                        os.path.join(settings.STATIC_ROOT or '', image_path),
                        os.path.join(settings.BASE_DIR, 'static', image_path),
                        os.path.join(settings.BASE_DIR, 'staticfiles', image_path),
                    ]
                    
                    photo_found = False
                    for static_image_path in possible_paths:
                        if os.path.exists(static_image_path):
                            try:
                                # Copy the image to media/contributor_photos/
                                from django.core.files import File
                                with open(static_image_path, 'rb') as f:
                                    filename = os.path.basename(image_path)
                                    contributor.photo.save(filename, File(f), save=True)
                                self.stdout.write(
                                    self.style.SUCCESS(f"✅ Created: {contributor.name} ({contributor.get_project_type_display()}) with photo")
                                )
                                photo_found = True
                                break
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f"⚠️  Could not copy photo for {contributor.name}: {str(e)}")
                                )
                    
                    if not photo_found:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Created: {contributor.name} ({contributor.get_project_type_display()}) - photo not found, please add manually via admin")
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Created: {contributor.name} ({contributor.get_project_type_display()}) - add photo via admin")
                    )
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating {data['name']}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n📊 Summary: {created_count} created, {skipped_count} skipped")
        )
        self.stdout.write(
            self.style.WARNING("Note: Some contributors may need photos uploaded manually via Django admin")
        )

