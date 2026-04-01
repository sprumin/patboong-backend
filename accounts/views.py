from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

User = get_user_model()


@extend_schema(
    tags=["accounts"],
    summary="회원가입",
    description="새로운 사용자를 등록합니다. 필수: 아이디, 비밀번호, 약관 동의 3개",
    request=RegisterSerializer,
    responses={201: UserSerializer},
    auth=[],
    examples=[
        OpenApiExample(
            "최소 필수 정보만",
            value={
                "user_id": "hong123",
                "user_pw": "Password123!@#",
                "service_terms": True,
                "privacy_terms": True,
                "age_terms": True,
            },
            request_only=True,
        ),
        OpenApiExample(
            "전체 정보 포함",
            value={
                "user_id": "hong456",
                "user_pw": "Password123!@#",
                "main_line": "mid",
                "sub_line": "top",
                "tier_top": "gold",
                "tier_jungle": "silver",
                "tier_mid": "platinum",
                "tier_adc": "bronze",
                "tier_support": "iron",
                "question": "pet",
                "answer": "멍멍이",
                "service_terms": True,
                "privacy_terms": True,
                "age_terms": True,
                "marketing_terms": False,
                "event_terms": False,
            },
            request_only=True,
        ),
    ],
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

@extend_schema(
    tags=["accounts"],
    summary="로그인",
    description="사용자 인증 후 JWT 토큰을 발급합니다.",
    request=LoginSerializer,
    auth=[],
    responses={
        200: {
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "Refresh Token"},
                "access": {"type": "string", "description": "Access Token"},
                "user": {"type": "object", "description": "사용자 정보"},
            },
        }
    },
    examples=[
        OpenApiExample(
            "로그인 요청 예시",
            value={"username": "hong123", "password": "Password123!@#"},
            request_only=True,
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )

    if user is None:
        return Response(
            {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
    )


@extend_schema(
    tags=["accounts"],
    summary="로그아웃",
    description="Refresh Token을 블랙리스트에 추가하여 로그아웃합니다.",
    request={
        "type": "object",
        "properties": {"refresh": {"type": "string", "description": "Refresh Token"}},
    },
    responses={200: {"description": "로그아웃 성공"}},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "로그아웃 되었습니다."})
    except Exception:
        return Response(
            {"detail": "유효하지 않은 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=["accounts"],
    summary="프로필 조회",
    description="현재 로그인한 사용자의 프로필 정보를 조회합니다. 비밀번호는 제외됩니다.",
    responses={200: UserSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
