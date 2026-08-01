from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .matching_views import TeamMatchingView
from .views import (
    RegisterView,
    friend_profile_view,
    friends_view,
    incoming_friend_requests_view,
    login_view,
    logout_view,
    match_detail_view,
    match_list_view,
    profile_view,
    refresh_riot_profile_view,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("profile/riot/refresh/", refresh_riot_profile_view, name="riot-profile-refresh"),
    path("friends/", friends_view, name="friends"),
    path("friends/incoming/", incoming_friend_requests_view, name="incoming-friends"),
    path("friends/<int:user_id>/", friend_profile_view, name="friend-profile"),
    path("matches/", match_list_view, name="matches"),
    path("matches/<str:match_id>/", match_detail_view, name="match-detail"),
    path("team-matching/", TeamMatchingView.as_view(), name="team-matching"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
