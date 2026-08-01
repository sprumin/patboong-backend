from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .matching import complete_settings, create_team_matches, get_matching_settings
from .matching_serializers import (
    DetailErrorSerializer,
    MatchingRecordDetailSerializer,
    MatchingRecordListResponseSerializer,
    MatchingRecordResultResponseSerializer,
    MatchingRecordResultUpdateSerializer,
    MatchingRecordSaveSerializer,
    MatchingSettingsErrorSerializer,
    MatchingSettingsResponseSerializer,
    MatchingSettingsSerializer,
    RecentParticipantsResponseSerializer,
    TeamMatchingRequestSerializer,
    TeamMatchingResponseSerializer,
)
from .models import (
    DEFAULT_POSITION_BONUS,
    DEFAULT_TIER_SCORES,
    MatchingRecord,
    MatchingRun,
    MatchingSettings,
    User,
)


MAX_SAVED_MATCHING_RECORDS = 5


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
    "matching_run_id": "11111111-1111-4111-8111-111111111111",
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

RECENT_PARTICIPANTS_EXAMPLE = {
    "matching_run_id": "11111111-1111-4111-8111-111111111111",
    "created_at": "2026-08-01T12:00:00+09:00",
    "participants": [
        {
            **TEAM_MATCHING_REQUEST_EXAMPLE["participants"][0],
            "is_current_user": True,
        },
        {
            "id": "guest-11111111",
            "name": "Guest#KR1",
            "primary_position": "top",
            "primary_tier": "Silver II",
            "secondary_position": "jungle",
            "secondary_tier": "Silver IV",
            "position_preference": "primary",
            "is_guest": True,
            "is_current_user": False,
        },
    ],
}

MATCHING_RECORD_DETAIL_EXAMPLE = {
    "id": "22222222-2222-4222-8222-222222222222",
    "team_number": 1,
    "balance_score": 100,
    "blue_total_score": 4000,
    "red_total_score": 4000,
    "score_difference": 0,
    "saved_at": "2026-08-01T12:00:00+09:00",
    "contains_current_user": True,
    "winning_team": "blue",
    "my_result": "win",
    "result_updated_at": "2026-08-01T12:30:00+09:00",
    "participants": RECENT_PARTICIPANTS_EXAMPLE["participants"],
    "blue_team": EXAMPLE_BLUE_TEAM,
    "red_team": EXAMPLE_RED_TEAM,
}


def _is_current_user(participant, user):
    return not participant.get("is_guest", False) and str(
        participant.get("id")
    ) == str(user.pk)


def _participants_for_response(participants, user):
    return [
        {**participant, "is_current_user": _is_current_user(participant, user)}
        for participant in participants
    ]


def _contains_current_user(participants, user):
    return any(_is_current_user(participant, user) for participant in participants)


def _current_user_team(record, user):
    if any(_is_current_user(participant, user) for participant in record.blue_team):
        return "blue"
    if any(_is_current_user(participant, user) for participant in record.red_team):
        return "red"
    return None


def _my_result(record, user):
    if record.winning_team is None:
        return None
    current_team = _current_user_team(record, user)
    if current_team is None:
        return None
    return "win" if current_team == record.winning_team else "loss"


def _record_detail(record, user):
    return {
        "id": record.id,
        "team_number": record.team_number,
        "balance_score": record.balance_score,
        "blue_total_score": record.blue_total_score,
        "red_total_score": record.red_total_score,
        "score_difference": record.score_difference,
        "saved_at": record.saved_at,
        "contains_current_user": _contains_current_user(record.participants, user),
        "winning_team": record.winning_team,
        "my_result": _my_result(record, user),
        "result_updated_at": record.result_updated_at,
        "participants": _participants_for_response(record.participants, user),
        "blue_team": record.blue_team,
        "red_team": record.red_team,
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
        normalized_participants = serializer.validated_data["participants"]
        result = create_team_matches(normalized_participants, get_matching_settings())
        with transaction.atomic():
            matching_run = MatchingRun.objects.create(
                owner=request.user,
                participants=normalized_participants,
                matches=result["matches"],
                unmatched_participants=result["unmatched_participants"],
            )
        return Response({"matching_run_id": matching_run.id, **result})


class RecentMatchingParticipantsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["accounts"],
        summary="직전 팀 매칭 참가자 조회",
        description=(
            "현재 사용자가 가장 최근 실행한 매칭의 원본 참가자를 입력 순서대로 "
            "반환합니다. 저장 여부와 무관하며 기록이 없으면 빈 목록을 반환합니다."
        ),
        responses={
            200: RecentParticipantsResponseSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                "최근 참가자",
                value=RECENT_PARTICIPANTS_EXAMPLE,
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "실행 기록 없음",
                value={
                    "matching_run_id": None,
                    "created_at": None,
                    "participants": [],
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request):
        matching_run = MatchingRun.objects.filter(owner=request.user).first()
        if matching_run is None:
            return Response(
                {
                    "matching_run_id": None,
                    "created_at": None,
                    "participants": [],
                }
            )
        return Response(
            {
                "matching_run_id": matching_run.id,
                "created_at": matching_run.created_at,
                "participants": _participants_for_response(
                    matching_run.participants, request.user
                ),
            }
        )


class MatchingRecordListCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["accounts"],
        operation_id="team_matching_records_list",
        summary="저장된 팀 매칭 기록 목록",
        description="현재 사용자의 저장 기록을 saved_at 내림차순으로 최대 5건 반환합니다.",
        responses={
            200: MatchingRecordListResponseSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                "저장 기록 목록",
                value={
                    "results": [
                        {
                            "id": "22222222-2222-4222-8222-222222222222",
                            "team_number": 1,
                            "balance_score": 100,
                            "saved_at": "2026-08-01T12:00:00+09:00",
                            "participant_count": 10,
                            "contains_current_user": True,
                            "winning_team": "blue",
                            "my_result": "win",
                            "result_updated_at": "2026-08-01T12:30:00+09:00",
                        }
                    ]
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def get(self, request):
        records = MatchingRecord.objects.filter(owner=request.user).order_by(
            "-saved_at", "-id"
        )[:MAX_SAVED_MATCHING_RECORDS]
        results = [
            {
                "id": record.id,
                "team_number": record.team_number,
                "balance_score": record.balance_score,
                "saved_at": record.saved_at,
                "participant_count": len(record.participants),
                "contains_current_user": _contains_current_user(
                    record.participants, request.user
                ),
                "winning_team": record.winning_team,
                "my_result": _my_result(record, request.user),
                "result_updated_at": record.result_updated_at,
            }
            for record in records
        ]
        return Response({"results": results})

    @extend_schema(
        tags=["accounts"],
        operation_id="team_matching_records_create",
        summary="팀 매칭 기록 저장",
        description=(
            "team-matching 응답의 matching_run_id와 저장할 team_number를 전달합니다. "
            "사용자별 최근 5건만 유지하며 초과 시 가장 오래된 기록을 같은 "
            "트랜잭션에서 삭제합니다. 동일 실행·팀을 다시 저장하면 기존 기록을 "
            "200으로 반환합니다."
        ),
        request=MatchingRecordSaveSerializer,
        responses={
            200: MatchingRecordDetailSerializer,
            201: MatchingRecordDetailSerializer,
            400: DetailErrorSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            404: DetailErrorSerializer,
            500: OpenApiResponse(description="서버 내부 오류가 발생했습니다."),
        },
        examples=[
            OpenApiExample(
                "첫 번째 매치 저장",
                value={
                    "matching_run_id": "11111111-1111-4111-8111-111111111111",
                    "team_number": 1,
                },
                request_only=True,
            ),
            OpenApiExample(
                "소유하지 않은 매칭 실행",
                value={"detail": "매칭 실행 기록을 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request):
        serializer = MatchingRecordSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            # Serializes all saves for one owner so concurrent requests cannot
            # exceed the per-user record limit.
            User.objects.select_for_update().get(pk=request.user.pk)
            matching_run = (
                MatchingRun.objects.select_for_update()
                .filter(
                    id=serializer.validated_data["matching_run_id"],
                    owner=request.user,
                )
                .first()
            )
            if matching_run is None:
                return Response(
                    {"detail": "매칭 실행 기록을 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            team_number = serializer.validated_data["team_number"]
            match = next(
                (
                    item
                    for item in matching_run.matches
                    if item["team_number"] == team_number
                ),
                None,
            )
            if match is None:
                return Response(
                    {"detail": "해당 매칭 실행에 존재하지 않는 팀 번호입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            start = (team_number - 1) * 10
            participants = matching_run.participants[start : start + 10]
            record, created = MatchingRecord.objects.get_or_create(
                owner=request.user,
                matching_run=matching_run,
                team_number=team_number,
                defaults={
                    "participants": participants,
                    "blue_team": match["blue_team"],
                    "red_team": match["red_team"],
                    "blue_total_score": match["blue_total_score"],
                    "red_total_score": match["red_total_score"],
                    "score_difference": match["score_difference"],
                    "balance_score": match["balance_score"],
                },
            )
            keep_ids = list(
                MatchingRecord.objects.filter(owner=request.user)
                .order_by("-saved_at", "-id")
                .values_list("id", flat=True)[:MAX_SAVED_MATCHING_RECORDS]
            )
            MatchingRecord.objects.filter(owner=request.user).exclude(
                id__in=keep_ids
            ).delete()
        return Response(
            _record_detail(record, request.user),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MatchingRecordDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["accounts"],
        operation_id="team_matching_record_retrieve",
        summary="저장된 팀 매칭 기록 상세",
        responses={
            200: MatchingRecordDetailSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            404: DetailErrorSerializer,
            500: OpenApiResponse(description="서버 내부 오류가 발생했습니다."),
        },
        examples=[
            OpenApiExample(
                "저장 기록 상세",
                value=MATCHING_RECORD_DETAIL_EXAMPLE,
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def get(self, request, record_id):
        record = MatchingRecord.objects.filter(
            id=record_id, owner=request.user
        ).first()
        if record is None:
            return Response(
                {"detail": "매칭 기록을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_record_detail(record, request.user))

    @extend_schema(
        tags=["accounts"],
        operation_id="team_matching_record_result_update",
        summary="저장된 매칭 경기 결과 설정",
        description=(
            "JWT 사용자와 저장된 팀 구성만을 기준으로 승리 팀을 계산합니다. "
            "my_result에 null을 전달하면 결과를 미정으로 되돌립니다."
        ),
        request=MatchingRecordResultUpdateSerializer,
        responses={
            200: MatchingRecordResultResponseSerializer,
            400: DetailErrorSerializer,
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            404: DetailErrorSerializer,
            500: OpenApiResponse(description="서버 내부 오류가 발생했습니다."),
        },
        examples=[
            OpenApiExample(
                "승리로 설정",
                value={"my_result": "win"},
                request_only=True,
            ),
            OpenApiExample(
                "경기 결과 응답",
                value={
                    "id": "22222222-2222-4222-8222-222222222222",
                    "winning_team": "blue",
                    "my_result": "win",
                    "result_updated_at": "2026-08-01T12:30:00+09:00",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "현재 사용자가 팀에 없음",
                value={"detail": "현재 사용자가 저장된 팀 구성에 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "잘못된 경기 결과",
                value={
                    "my_result": [
                        "경기 결과는 win, loss 또는 null만 사용할 수 있습니다."
                    ]
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def patch(self, request, record_id):
        serializer = MatchingRecordResultUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            record = (
                MatchingRecord.objects.select_for_update()
                .filter(id=record_id, owner=request.user)
                .first()
            )
            if record is None:
                return Response(
                    {"detail": "매칭 기록을 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            current_team = _current_user_team(record, request.user)
            if current_team is None:
                return Response(
                    {"detail": "현재 사용자가 저장된 팀 구성에 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            my_result = serializer.validated_data["my_result"]
            if my_result is None:
                record.winning_team = None
                record.result_updated_at = None
            else:
                record.winning_team = (
                    current_team
                    if my_result == "win"
                    else "red" if current_team == "blue" else "blue"
                )
                record.result_updated_at = timezone.now()
            record.save(update_fields=["winning_team", "result_updated_at"])

        return Response(
            {
                "id": record.id,
                "winning_team": record.winning_team,
                "my_result": _my_result(record, request.user),
                "result_updated_at": record.result_updated_at,
            }
        )

    @extend_schema(
        tags=["accounts"],
        operation_id="team_matching_record_destroy",
        summary="저장된 팀 매칭 기록 삭제",
        responses={
            204: OpenApiResponse(description="매칭 기록이 삭제되었습니다."),
            401: OpenApiResponse(description="JWT 인증이 필요합니다."),
            404: DetailErrorSerializer,
            500: OpenApiResponse(description="서버 내부 오류가 발생했습니다."),
        },
        examples=[
            OpenApiExample(
                "기록 없음 또는 소유권 없음",
                value={"detail": "매칭 기록을 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            )
        ],
    )
    def delete(self, request, record_id):
        deleted, _ = MatchingRecord.objects.filter(
            id=record_id, owner=request.user
        ).delete()
        if not deleted:
            return Response(
                {"detail": "매칭 기록을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
