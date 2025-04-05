from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    ContactListView,
    BulkContactCreateView,
    SpamReportListView,
    SearchByNameView,
    SearchByPhoneView,
    WelcomeView
)

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('contacts/', ContactListView.as_view(), name='contact-list'),
    path('contacts/bulk_create/', BulkContactCreateView.as_view(), name='bulk-contact-create'),
    path('spam-reports/', SpamReportListView.as_view(), name='spam-report-list'),
    path('search/', SearchByNameView.as_view(), name='search-by-name'),
    path('search/phone/', SearchByPhoneView.as_view(), name='search-by-phone'),
]