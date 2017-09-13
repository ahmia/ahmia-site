from ahmia.models import HiddenWebsite


for address in HiddenWebsite.objects.all():
    address.delete()

