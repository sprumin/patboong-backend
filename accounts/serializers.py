from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "main_line",
            "sub_line",
            "tier_top",
            "tier_jungle",
            "tier_mid",
            "tier_adc",
            "tier_support",
            "question",
            "answer",
            "service_terms",
            "privacy_terms",
            "age_terms",
            "marketing_terms",
            "event_terms",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class RegisterSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="username", required=True)
    user_pw = serializers.CharField(
        source="password",
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    main_line = serializers.CharField(required=False, allow_blank=True, default="")
    sub_line = serializers.CharField(required=False, allow_blank=True, default="")
    tier_top = serializers.CharField(required=False, allow_blank=True, default="")
    tier_jungle = serializers.CharField(required=False, allow_blank=True, default="")
    tier_mid = serializers.CharField(required=False, allow_blank=True, default="")
    tier_adc = serializers.CharField(required=False, allow_blank=True, default="")
    tier_support = serializers.CharField(required=False, allow_blank=True, default="")
    question = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)
    service_terms = serializers.BooleanField(required=True)
    privacy_terms = serializers.BooleanField(required=True)
    age_terms = serializers.BooleanField(required=True)
    marketing_terms = serializers.BooleanField(required=False, default=False)
    event_terms = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = (
            "user_id",
            "user_pw",
            "main_line",
            "sub_line",
            "tier_top",
            "tier_jungle",
            "tier_mid",
            "tier_adc",
            "tier_support",
            "question",
            "answer",
            "service_terms",
            "privacy_terms",
            "age_terms",
            "marketing_terms",
            "event_terms",
        )

    def validate(self, attrs):
        if not attrs.get("service_terms"):
            raise serializers.ValidationError(
                {"service_terms": "서비스 이용약관 동의는 필수입니다."}
            )
        if not attrs.get("privacy_terms"):
            raise serializers.ValidationError(
                {"privacy_terms": "개인정보 수집 동의는 필수입니다."}
            )
        if not attrs.get("age_terms"):
            raise serializers.ValidationError(
                {"age_terms": "만 14세 이상 확인은 필수입니다."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
