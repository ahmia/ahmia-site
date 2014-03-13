from django.conf.urls.defaults import *
from django.conf import settings

#for admin UI
from django.contrib import admin
admin.autodiscover()


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    #is domain up
    (r'^address/([a-z2-7]{16})/status', 'ahmia.views.onion_up' ), #domain:port/address/3g2upl4pq6kufc4m/up
    #edit hidden service
    (r'^address/([a-z2-7]{16})/edit/', 'ahmia.views.onion_edit' ), #domain:port/address/3g2upl4pq6kufc4m/edit
    #/address/ API
    (r'^address/([a-z2-7]{16})', 'ahmia.views.onion' ), #domain:port/address/3g2upl4pq6kufc4m
    #invalid /address url
    (r'^address/(.+)', 'ahmia.views.onion_error' ), #invalid /address/ url
    #GET lists every known HS and POST adds a new HS
    (r'^address/', 'ahmia.views.onion_list' ), #domain:port/address/

    #login and logout
    (r'^rule/login/', 'ahmia.views.login' ), 
    (r'^rule/logout/', 'ahmia.views.logout' ), 
    #Rule content
    (r'^rule/$', 'ahmia.views.rule' ),

    #blackday JavaScript 
    (r'^blackday.js', 'ahmia.views.blackday' ),

    #our policy
    (r'^policy/', 'ahmia.views.policy' ),

    #disclaimer text
    (r'^disclaimer/', 'ahmia.views.disclaimer' ),

    #documentation - create hidden service description to hidden services
    (r'^documentation/createHsDescription/', 'ahmia.views.createHsDescription' ),

    #documentation - description proposal to hidden services
    (r'^documentation/descriptionProposal/', 'ahmia.views.descriptionProposal' ),

    #banned hidden services (MD5)
    (r'^banned/', 'ahmia.views.banned' ),

    #documentation
    (r'^documentation/', 'ahmia.views.documentation' ),

    #about us
    (r'^about/', 'ahmia.views.about' ),

    #show IP
    (r'^IP/', 'ahmia.views.show_ip' ),

    #full text search
    (r'^search', 'ahmia.views.search_page' ),

    #full text search
    (r'^query', 'ahmia.views.query' ),

    #search without JavaScript
    (r'^find/(.*)', 'ahmia.views.find' ),

    (r'^admin/', include(admin.site.urls)), #for admin UI

    #plain texts list of onion urls
    (r'^onions/', 'ahmia.views.onions_txt' ),
    (r'^oniondomains\.txt$', 'ahmia.views.onions_txt' ),

    #MD5 list of banned onion urls
    (r'^bannedMD5\.txt$', 'ahmia.views.banned' ),

    #plain texts list of banned onion urls
    (r'^banneddomains\.txt$', 'ahmia.views.banned_domains_plain' ),

    #plain texts list of banned onion urls
    (r'^alldomains', 'ahmia.views.all_onions_txt' ),

    #favicon.ico
    (r'^favicon\.ico$', 'django.views.generic.base.RedirectView', {'url': '/static/images/favicon.ico'}),

    #add domain form
    (r'^add/', 'ahmia.views.add' ), #domain:port/add

    (r'^$', 'ahmia.views.default' ), #domain:port

    # Example:
    # (r'^ahmia/', include('ahmia.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)


#media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
