from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import LoginView, LogoutView
from apps.invoices.views import invoice_list
from core.views import deploy


urlpatterns = [
    path('deploy/<str:token>/', deploy, name='deploy'),
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('apps.accounts.urls')),
    path('', invoice_list, name='home'),
    path('', include('apps.services.urls')),
    path('', include('apps.invoices.urls')),
    path('', include('apps.labels.urls')),
]
