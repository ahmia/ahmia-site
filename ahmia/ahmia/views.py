"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import AddOnionForm, ReportOnionForm

class CoreView(TemplateView):
    """Core page of the website."""
    http_method_names = ['get']

class HomepageView(CoreView):
    """The homepage."""
    template_name = "index_tor.html"

class InvisibleInternetView(CoreView):
    """The main i2p search page."""
    template_name = "index_i2p.html"

class LegalView(CoreView):
    """Static legal page."""
    template_name = "legal.html"

class DocumentationView(CoreView):
    """Static documentation page."""
    template_name = "documentation.html"

class IndexingDocumentationView(CoreView):
    """Static page about the indexing and crawling."""
    template_name = "indexing.html"

class DescPropDocumentationView(CoreView):
    """Static description proposal."""
    template_name = "descriptionProposal.html"

class CreateDescDocumentationView(CoreView):
    """Page to create hidden website description."""
    template_name = "createHsDescription.html"

class AboutView(CoreView):
    """Static about page."""
    template_name = "about.html"

class GsocView(CoreView):
    """Summer of code 2014."""
    template_name = "gsoc.html"

class AddView(FormView):
    """Add form for a new .onion address."""
    form_class = AddOnionForm
    success_url = "/add/success/"
    template_name = "add.html"

    def form_valid(self, form):
        form.send_new_onion()
        return super(AddView, self).form_valid(form)

class AddSuccessView(CoreView):
    """Onion successfully added."""
    template_name = "add_success.html"

class BlacklistView(FormView):
    """Return a blacklist page with MD5 sums of banned content."""
    form_class = ReportOnionForm
    success_url = "/blacklist/success/"
    template_name = "blacklist.html"

    def form_valid(self, form):
        form.send_abuse_report()
        return super(BlacklistView, self).form_valid(form)

class BlacklistSuccessView(CoreView):
    """Onion successfully reported."""
    template_name = "blacklist_success.html"
