from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import LoginView, LogoutView
from apps.services.views import service_call_list


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('apps.accounts.urls')),
    path('', service_call_list, name='home'),
    path('', include('apps.services.urls')),
    path('', include('apps.invoices.urls')),
    path('', include('apps.associations.urls')),
    path('', include('apps.labels.urls')),
]
