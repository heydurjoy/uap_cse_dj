from django.core.management.base import BaseCommand
from people.models import Contributor


class Command(BaseCommand):
    help = 'Update Contributor model with GitHub contribution statistics'
    
    def handle(self, *args, **options):
        # GitHub contribution data
        github_stats = [
            {
                'github_username': 'Tahiya07',
                'commits': 47,
                'lines_added': 9630,
                'lines_deleted': 5366,
            },
            {
                'github_username': 'heydurjoy',
                'commits': 36,
                'lines_added': 4354,
                'lines_deleted': 2842,
            },
            {
                'github_username': 'JunHossain',
                'commits': 19,
                'lines_added': 753,
                'lines_deleted': 463,
            },
            {
                'github_username': 'Wasikul-Fahim',
                'commits': 15,
                'lines_added': 1049,
                'lines_deleted': 1016,
            },
            {
                'github_username': 'Yeamin-Bhuiyan',
                'commits': 13,
                'lines_added': 2765,
                'lines_deleted': 524,
            },
            {
                'github_username': 'lubabahasan',
                'commits': 10,
                'lines_added': 836,
                'lines_deleted': 338,
            },
            {
                'github_username': 'TasniaSami123',
                'commits': 9,
                'lines_added': 497,
                'lines_deleted': 239,
            },
            {
                'github_username': 'ibrahim-hasan5',
                'commits': 7,
                'lines_added': 727,
                'lines_deleted': 123,
            },
            {
                'github_username': 'Fabia44',
                'commits': 7,
                'lines_added': 396,
                'lines_deleted': 45,
            },
            {
                'github_username': 'Md-Sahriar-Asif',
                'commits': 6,
                'lines_added': 369,
                'lines_deleted': 22,
            },
            {
                'github_username': 'Faizun12',
                'commits': 5,
                'lines_added': 813,
                'lines_deleted': 10,
            },
            {
                'github_username': 'Anim36',
                'commits': 5,
                'lines_added': 567,
                'lines_deleted': 917,
            },
            {
                'github_username': 'ShazuMiu',
                'commits': 4,
                'lines_added': 226,
                'lines_deleted': 27,
            },
            {
                'github_username': 'MarzzzSiam',
                'commits': 3,
                'lines_added': 285,
                'lines_deleted': 40,
            },
            {
                'github_username': 'Akifhossain29',
                'commits': 2,
                'lines_added': 247,
                'lines_deleted': 3,
            },
        ]
        
        updated_count = 0
        not_found_count = 0
        
        for stats in github_stats:
            github_username = stats['github_username']
            
            # Find contributors by github_username (case-insensitive)
            contributors = Contributor.objects.filter(
                github_username__iexact=github_username
            )
            
            if contributors.exists():
                # Update all matching contributors (in case someone appears in both sections)
                for contributor in contributors:
                    contributor.number_of_commits = stats['commits']
                    contributor.lines_added = stats['lines_added']
                    contributor.lines_deleted = stats['lines_deleted']
                    contributor.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Updated: {contributor.name} ({contributor.get_project_type_display()}) - "
                            f"{stats['commits']} commits, +{stats['lines_added']} / -{stats['lines_deleted']} lines"
                        )
                    )
                    updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Not found: {github_username} - skipping"
                    )
                )
                not_found_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Summary: {updated_count} contributors updated, {not_found_count} usernames not found"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Note: Make sure to set github_username field in Django admin for contributors"
            )
        )

