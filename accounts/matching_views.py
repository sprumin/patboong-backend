from django.db import transaction
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .matching import complete_settings, create_team_matches, get_matching_settings
from .matching_serializers import (
    DetailErrorSerializer,
    MatchingSettingsErrorSerializer,
    MatchingSettingsResponseSerializer,
    MatchingSettingsSerializer,
    TeamMatchingRequestSerializer,
    TeamMatchingResponseSerializer,
)
from .models import DEFAULT_POSITION_BONUS, DEFAULT_TIER_SCORES, MatchingSettings


SETTINGS_EXAMPLE = {
    "tier_scores": {
        "Iron IV": 100,
        "Gold II": 800,
        "Challenger": 1700,
    },
    "position_bonus": {
        "top": 0,
        "jungle": 5,
        "mid": 0,
        "adc": 3,
        "support": 0,
    },
}

FULL_SETTINGS_EXAMPLE = {
    "tier_scores": DEFAULT_TIER_SCORES,
    "position_bonus": DEFAULT_POSITION_BONUS,
}

TEAM_MATCHING_REQUEST_EXAMPLE = {
    "participants": [
        {
            "id": index,
            "name": f"Player{index}#KR1",
            "primary_position": position,
            "primary_tier": "Gold II",
            "secondary_position": "adc" if position != "adc" else "mid",
            "secondary_tier": "Gold IV",
            "position_preference": "primary",
            "is_guest": False,
        }
        for index, position in enumerate(
            ("top", "jungle", "mid", "adc", "support") * 2, start=1
        )
    ]
}

EXAMPLE_BLUE_TEAM = [
    {
        "id": index,
        "name": f"Player{index}#KR1",
        "assigned_position": position,
        "used_tier": "Gold II",
        "score": 800,
        "is_guest": False,
    }
    for index, position in enumerate(
        ("top", "jungle", "mid", "adc", "support"), start=1
    )
]
EXAMPLE_RED_TEAM = [
    {
        "id": index,
        "name": f"Player{index}#KR1",
        "assigned_position": position,
        "used_tier": "Gold II",
        "score": 800,
        "is_guest": False,
    }
    for index, position in enumerate(
        ("top", "jungle", "mid", "adc", "support"), start=6
    )
]
TEAM_MATCHING_RESPONSE_EXAMPLE = {
    "matches": [
        {
            "team_number": 1,
            "blue_team": EXAMPLE_BLUE_TEAM,
            "red_team": EXAMPLE_RED_TEAM,
            "blue_total_score": 4000,
            "red_total_score": 4000,
            "score_difference": 0,
            "balance_score": 100,
        }
    ],
    "unmatched_participants": [],
}


class MatchingSettingsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["admin"],
        summary="매칭 점수 설정 조회",
        description=(
            "티어별 기본 점수와 포지션별 가산점(0~100%)을 조회합니다. "
            "저장된 설정이 없으면 기본 설정을 반환합니다."
        ),
        responses={
            200: MatchingSettingsResponseSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            403: OpenApiResponse(description="관리자 권한이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                "기본 매칭 설정",
                value=FULL_SETTINGS_EXAMPLE,
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def get(self, request):
        return Response(get_matching_settings())

    @extend_schema(
        tags=["admin"],
        summary="매칭 점수 설정 저장",
        description=(
            "전달된 티어와 포지션만 기존 전체 설정에 안전하게 병합합니다. "
            "티어 점수는 0 이상의 정수, 포지션 가산점은 0~100의 정수입니다."
        ),
        request=MatchingSettingsSerializer,
        responses={
            200: MatchingSettingsResponseSerializer,
            400: OpenApiResponse(
                response=MatchingSettingsErrorSerializer,
                description="설정 키 또는 값이 잘못되었습니다.",
            ),
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            403: OpenApiResponse(description="관리자 권한이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                "매칭 설정 변경",
                value=SETTINGS_EXAMPLE,
                request_only=True,
            ),
            OpenApiExample(
                "알 수 없는 설정 키",
                value={"tier_scores": {"Mythic": ["Unknown tier."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def put(self, request):
        serializer = MatchingSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            instance = MatchingSettings.objects.select_for_update().filter(pk=1).first()
            merged = complete_settings(instance)
            for field, values in serializer.validated_data.items():
                merged[field].update(values)

            if instance is None:
                instance = MatchingSettings(pk=1)
            instance.tier_scores = merged["tier_scores"]
            instance.position_bonus = merged["position_bonus"]
            instance.save()

        return Response(complete_settings(instance))


class TeamMatchingView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["accounts"],
        summary="LoL 내전 팀 매칭",
        description=(
            "참가자를 입력 순서대로 10명씩 묶어 5대5 팀을 생성합니다. "
            "양 팀의 포지션 구성을 우선한 뒤 총점 차이가 가장 작은 조합을 "
            "선택합니다. 10명 미만으로 남은 참가자는 unmatched_participants로 "
            "반환합니다. balance_score는 100 × (1 - 점수 차이 / 높은 팀 점수)이며 "
            "0~100 범위입니다."
        ),
        request=TeamMatchingRequestSerializer,
        responses={
            200: TeamMatchingResponseSerializer,
            400: OpenApiResponse(
                response=DetailErrorSerializer,
                description="참가자 수 또는 입력값이 잘못되었습니다.",
            ),
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                "팀 매칭 요청",
                value=TEAM_MATCHING_REQUEST_EXAMPLE,
                request_only=True,
            ),
            OpenApiExample(
                "팀 매칭 성공",
                value=TEAM_MATCHING_RESPONSE_EXAMPLE,
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "참가자 부족",
                value={"detail": "팀 매칭에는 최소 10명의 참가자가 필요합니다."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        participants = request.data.get("participants")
        if isinstance(participants, list) and len(participants) < 10:
            return Response(
                {"detail": "팀 매칭에는 최소 10명의 참가자가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TeamMatchingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_team_matches(
            serializer.validated_data["participants"], get_matching_settings()
        )
        return Response(result)
