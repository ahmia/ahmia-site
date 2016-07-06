"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .models import HiddenWebsite, HiddenWebsiteDescription
from .forms import AddOnionForm

class HomepageView(TemplateView):
    """The homepage."""
    http_method_names = ['get']
    template_name = "index_tor.html"

class IipView(TemplateView):
    """The main i2p search page."""
    http_method_names = ['get']
    template_name = "index_i2p.html"

class AhmiaPage(TemplateView):
    """Core page of the website."""
    http_method_names = ['get']

    def latest_descriptions(self, onions):
        """Return the latest descriptions to these onion objects."""
        #The old implementatation was working only with PostgreSQL database
        #desc = HiddenWebsiteDescription.objects.order_by('about', '-updated')
        #desc = desc.distinct('about')
        # Select the onions related to the descriptions
        descriptions = HiddenWebsiteDescription.objects.select_related("about")
        # Select only the onions, online ones
        descriptions = descriptions.filter(about__in=onions)
        # Order the results
        descriptions = descriptions.order_by('about', '-updated')
        descs = []
        last_onion = "" # The latest onion selected
        # Select the first (the latest) from each onion group
        for desc in descriptions:
            if last_onion != desc.about.id:
                last_onion = desc.about.id
                desc.url = desc.about.url
                desc.hs_id = desc.about.id
                desc.banned = desc.about.banned
                descs.append(desc)
        return descs

    def get_context_data(self, **kwargs):
        onions = HiddenWebsite.objects.filter(online=True)
        return {
            "count_banned": onions.filter(banned=True).count(),
            "count_online": onions.filter(banned=False).count()
        }

class LegalView(AhmiaPage):
    """Static legal page."""
    template_name = "legal.html"

class DocumentationView(AhmiaPage):
    """Static documentation page."""
    template_name = "documentation.html"

class IndexingDocumentationView(AhmiaPage):
    """Static page about the indexing and crawling."""
    template_name = "indexing.html"

class DescPropDocumentationView(AhmiaPage):
    """Static description proposal."""
    template_name = "descriptionProposal.html"

class CreateDescDocumentationView(AhmiaPage):
    """Page to create hidden website description."""
    template_name = "createHsDescription.html"

class AboutView(AhmiaPage):
    """Static about page."""
    template_name = "about.html"

class GsocView(AhmiaPage):
    """Summer of code 2014."""
    template_name = "gsoc.html"

class AddView(FormView):
    """Add form for a new .onion address."""
    form_class = AddOnionForm
    template_name = "add.html"

    def form_valid(self, form):
        form.add_onion()
        return super(AddView, self).form_valid(form)


class ReportView(FormView):
    """Return a request page to blacklist a site."""
    form_class = AddOnionForm
    template_name = "blacklist_report.html"

    def form_valid(self, form):
        return super(ReportView, self).form_valid(form)


class BlacklistView(FormView):
    """Return a blacklist page with MD5 sums of banned content."""
    form_class = AddOnionForm
    template_name = "blacklist.html"

    def form_valid(self, form):
        return super(BlacklistView, self).form_valid(form)



'''@require_http_methods(['GET', 'POST'])
def blacklist_report(request):
    """Return a request page to blacklist a site."""
    if request.method == 'POST':
        if 'onion' in request.POST \
           and is_valid_onion(request.POST['onion']):
            send_abuse_report(request.POST['onion'])
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})
    else:
        if 'onion' in request.GET \
           and is_valid_onion(request.GET['onion']):
            send_abuse_report(request.GET['onion'])
            onion = request.GET['onion']
            success = True
        else:
            onion = ''
            success = False
        content = Context({
            'success': success,
            'onion': onion
        })
        template = loader.get_template('blacklist_report.html')
        return HttpResponse(template.render(content))

@require_GET
def blacklist(request):
    """Return a blacklist page with MD5 sums of banned content."""
    try:
        banned_onions = HiddenWebsite.objects.all().filter(banned=True)
    except HiddenWebsite.DoesNotExist:
        banned_onions = []
    content = Context({'banned_onions': banned_onions})
    template = loader.get_template('blacklist.html')
    return HttpResponse(template.render(content))'''
