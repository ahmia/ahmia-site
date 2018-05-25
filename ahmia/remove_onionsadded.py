from ahmia.models import HiddenWebsite


for address in HiddenWebsite.objects.all():
    address.delete()

# todo make this a manage.py command
