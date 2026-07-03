from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.views import LoginView, LogoutView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('apps.accounts.urls')),
    path('', RedirectView.as_view(url='/service-calls/', permanent=False), name='home'),
    path('', include('apps.services.urls')),
    path('', include('apps.invoices.urls')),
    path('', include('apps.associations.urls')),
    path('', include('apps.labels.urls')),
]
