""" Import banned CSAM onion websites:
python manage.py importcsamdetections --file csam_detection/new_banned_onions.txt
"""
import re
from django.core.management.base import BaseCommand, CommandError
from ahmia.models import BannedWebsite
from django.core.exceptions import ValidationError

def validate_onion(onion):
    """Test if a url is a valid hiddenservice domain"""
    if not onion.endswith('.onion'):
        raise ValidationError((f"{onion} is not a valid onion address"))
    main_onion_domain_part = onion.split('.')[-2]
    if not re.match(r'^[a-z2-7]{56}$', main_onion_domain_part):
        raise ValidationError((f"{onion} is not a valid onion address"))

class Command(BaseCommand):
    help = 'Import .onion domains into the BannedWebsite model'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the file with onion domains')

    def handle(self, *args, **options):
        file_path = options['file']
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    domain = line.strip().split(' ')[0]
                    if domain:
                        try:
                            validate_onion(domain)
                            BannedWebsite.objects.get_or_create(onion=domain)
                            self.stdout.write(self.style.SUCCESS(f'Added: {domain}'))
                        except ValidationError as e:
                            self.stderr.write(f'Validation error: {domain} — {e}')
                        except Exception as e:
                            self.stderr.write(f'Error adding {domain}: {e}')
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
