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
    description="새로운 사용자를 등록합니다. 롤 듀오 매칭을 위한 게임 정보와 약관 동의가 필요합니다.",
    request=RegisterSerializer,
    responses={201: UserSerializer},
    examples=[
        OpenApiExample(
            "회원가입 예시",
            value={
                "userId": "hong123",
                "userPw": "password123!@",
                "mainLine": "mid",
                "subLine": "top",
                "tierTop": "gold",
                "tierJungle": "silver",
                "tierMid": "platinum",
                "tierAdc": "bronze",
                "tierSupport": "iron",
                "question": "pet",
                "answer": "멍멍이",
                "serviceTerms": True,
                "privacyTerms": True,
                "ageTerms": True,
                "marketingTerms": False,
                "eventTerms": False,
            },
            request_only=True,
        )
    ],
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@extend_schema(
    tags=["accounts"],
    summary="로그인",
    description="사용자 인증 후 JWT 토큰을 발급합니다.",
    request=LoginSerializer,
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
            value={"username": "hong123", "password": "password123!@"},
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
