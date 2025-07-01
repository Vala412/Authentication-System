from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls', namespace='main')),  # Add namespace here
    path('accounts/', include('accounts.urls', namespace='accounts')),  # Also add namespace for accounts
]

# Add internationalization patterns if needed
urlpatterns += i18n_patterns(
    path('', include('main.urls', namespace='main')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
)