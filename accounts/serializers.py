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


class RegisterSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    user_pw = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password],
    )
    main_line = serializers.CharField(required=False, allow_blank=True, default="")
    sub_line = serializers.CharField(required=False, allow_blank=True, default="")
    tier_top = serializers.CharField(required=False, allow_blank=True, default="")
    tier_jungle = serializers.CharField(required=False, allow_blank=True, default="")
    tier_mid = serializers.CharField(required=False, allow_blank=True, default="")
    tier_adc = serializers.CharField(required=False, allow_blank=True, default="")
    tier_support = serializers.CharField(required=False, allow_blank=True, default="")
    question = serializers.CharField(required=False, allow_blank=True, default="")
    answer = serializers.CharField(required=False, allow_blank=True, default="")
    service_terms = serializers.BooleanField(required=True)
    privacy_terms = serializers.BooleanField(required=True)
    age_terms = serializers.BooleanField(required=True)
    marketing_terms = serializers.BooleanField(required=False, default=False)
    event_terms = serializers.BooleanField(required=False, default=False)

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
        user_id = validated_data.pop("user_id")
        user_pw = validated_data.pop("user_pw")
        
        user = User.objects.create_user(
            username=user_id,
            password=user_pw,
            email="",
            main_line=validated_data.get("main_line", ""),
            sub_line=validated_data.get("sub_line", ""),
            tier_top=validated_data.get("tier_top", ""),
            tier_jungle=validated_data.get("tier_jungle", ""),
            tier_mid=validated_data.get("tier_mid", ""),
            tier_adc=validated_data.get("tier_adc", ""),
            tier_support=validated_data.get("tier_support", ""),
            question=validated_data.get("question", ""),
            answer=validated_data.get("answer", ""),
            service_terms=validated_data.get("service_terms", False),
            privacy_terms=validated_data.get("privacy_terms", False),
            age_terms=validated_data.get("age_terms", False),
            marketing_terms=validated_data.get("marketing_terms", False),
            event_terms=validated_data.get("event_terms", False),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
