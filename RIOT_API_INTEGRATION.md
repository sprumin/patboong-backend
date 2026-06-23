# Riot API 적용 방법

## 1. Riot API Key 발급

1. https://developer.riotgames.com 에 접속합니다.
2. Riot 계정으로 로그인합니다.
3. 로그인하면 기본 Development API Key가 자동 발급됩니다.
4. 개발용 키는 24시간마다 만료되므로, 개발 중에는 포털에서 주기적으로 재발급해야 합니다.
5. 실제 서비스용이면 Developer Portal에서 `Register Product` 또는 `Register Project`로 프로젝트를 등록하고 Personal/Production Key 승인을 받아야 합니다.

참고: Riot 공식 문서 기준으로 Development Key는 임시 키이며 24시간마다 비활성화됩니다. Production Key는 공개 서비스용으로 별도 신청이 필요합니다.

## 2. 백엔드 환경변수 적용

프로젝트 루트의 `.env`에 Riot 키를 넣습니다.

```env
RIOT_API_KEY=RGAPI-발급받은_키
RIOT_API_TIMEOUT=10
```

주의:

- `.env`는 Git에 올리면 안 됩니다.
- 프론트엔드에 `RIOT_API_KEY`를 절대 넣지 않습니다.
- 프론트는 Riot API를 직접 호출하지 않고 백엔드 API만 호출합니다.

## 3. 이 코드에서 사용되는 위치

환경변수는 [config/settings.py](config/settings.py)에서 읽습니다.

```python
RIOT_API_KEY = config("RIOT_API_KEY", default="")
RIOT_API_TIMEOUT = config("RIOT_API_TIMEOUT", default=10, cast=int)
```

실제 Riot 호출은 [accounts/riot.py](accounts/riot.py)에서 처리합니다.

```python
headers={
    "X-Riot-Token": self.api_key,
    "Accept": "application/json",
}
```

즉 적용 흐름은 아래와 같습니다.

```text
.env
 -> config/settings.py
 -> accounts/riot.py RiotClient
 -> 회원가입 / 프로필수정 / 전적조회 API
```

## 4. 현재 구현된 Riot 연동 API

회원가입:

```http
POST /api/accounts/register/
```

요청에 아래 값을 포함하면 백엔드가 Riot API로 검증하고 `puuid`를 저장합니다.

```json
{
  "riot_game_name": "hide on bush",
  "riot_tag_line": "KR1",
  "riot_server": "ASIA"
}
```

프로필 수정:

```http
PATCH /api/accounts/profile/
```

Riot ID가 변경되면 백엔드가 다시 검증하고 `puuid`, `verified_at`을 갱신합니다.

전적 조회:

```http
GET /api/accounts/matches/?start=0&count=20
GET /api/accounts/matches/{match_id}/
```

백엔드가 저장된 `puuid`로 Riot Match API를 호출합니다.

## 5. 서버 값

Account-V1, Match-V5는 지역 라우팅을 사용합니다.

한국 계정 기준:

```json
{
  "riot_server": "ASIA"
}
```

현재 허용값:

```text
ASIA, AMERICAS, EUROPE, SEA
```

## 6. 관련 Riot 공식 문서

- Developer Portal: https://developer.riotgames.com/docs/portal
- Account by Riot ID: https://developer.riotgames.com/apis#account-v1/GET_getByRiotId
- Account by PUUID: https://developer.riotgames.com/apis#account-v1/GET_getByPuuid
- Match IDs by PUUID: https://developer.riotgames.com/apis#match-v5/GET_getMatchIdsByPUUID
- Match by Match ID: https://developer.riotgames.com/apis#match-v5/GET_getMatch
