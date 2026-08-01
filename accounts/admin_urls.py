from django.urls import path

from .matching_views import MatchingSettingsView


urlpatterns = [
    path("matching-settings/", MatchingSettingsView.as_view(), name="matching-settings"),
]
