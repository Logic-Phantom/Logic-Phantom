# 🎨 Daily Theme Rotation

프로필 README의 **레이아웃(구성)과 컬러 테마를 매일 12:00 KST에 자동으로 바꾸는** 시스템입니다.
루트 `README.md`는 매일 이 폴더의 파일들로부터 다시 생성되므로 **직접 수정하지 마세요.**

## 구조

```
.github/
├── theme/
│   ├── profile.json      ← 콘텐츠 (타이핑 문구, 소개, 기술스택, 연락처, 인용구)
│   ├── themes.json       ← 컬러 테마 15종
│   ├── layouts/*.md      ← 레이아웃 5종 ({{block}} 토큰으로 구성)
│   ├── render.py         ← 오늘의 레이아웃 + 테마를 골라 README.md 생성
│   └── current.json      ← 오늘 적용된 조합 (snake.yml이 뱀 색상으로 사용)
└── workflows/
    ├── daily-theme.yml           ← 매일 12:00 KST: README 렌더 → 커밋/푸시 → 뱀 재생성
    ├── snake.yml                 ← 뱀 애니메이션 (12시간마다 + daily-theme에서 호출)
    └── profile-summary-cards.yml ← 매일 65개 테마의 통계 카드를 생성 (기존)
```

## 동작 원리

1. `profile-summary-cards.yml`이 매일 `profile-summary-card-output/<테마>/`에 **모든 테마의 카드**를 미리 만들어 둡니다.
   그래서 README가 어느 테마 폴더를 가리키느냐만 바꾸면 카드 디자인이 바뀝니다.
2. `daily-theme.yml`이 03:00 UTC(12:00 KST)에 `render.py`를 실행합니다.
   - 날짜(KST) 기준으로 **레이아웃**과 **테마**를 각각 독립적으로 고릅니다.
   - 각 목록은 한 사이클 동안 모두 한 번씩 등장하고, 사이클마다 순서를 새로 섞으며, 같은 항목이 이틀 연속 나오지 않습니다.
   - 선택은 날짜로 결정되므로 같은 날 여러 번 실행해도 결과가 같습니다.
3. 생성된 `README.md`와 `current.json`을 봇 계정으로 커밋·푸시합니다.
4. `GITHUB_TOKEN`으로 한 푸시는 다른 워크플로우를 트리거하지 않으므로, 같은 워크플로우에서 `snake.yml`을 직접 호출해
   `current.json`의 팔레트로 뱀을 다시 그려 `output` 브랜치에 올립니다.

## 레이아웃 5종

| id | 특징 |
|---|---|
| `classic` | 기존 구성 그대로 (섹션 헤더 + 기술스택 표 + 카드 5종) |
| `hero` | 이름이 들어간 대형 캡슐 배너, 통계 카드 우선, flat-square 뱃지 |
| `dashboard` | 2단 표: 왼쪽 소개·스택 / 오른쪽 통계 카드, 연락처가 상단 |
| `terminal` | `$ whoami` 형식 헤더, 소개를 TypeScript 코드블록으로 표시 |
| `minimal` | 중앙 정렬 한 줄 흐름, 섹션 헤더 없는 컴팩트 구성 |

## 컬러 테마 15종

Violet Phantom · Tokyo Night · Dracula · Nord Aurora · Rosé Pine · Synthwave '84 · Solarized · Gruvbox ·
Neon 2077 · Deep Ocean · Emerald Forest · Aura · Monokai Pro · Catppuccin Mocha · Graphite Mono

테마마다 다음을 정의합니다 (`themes.json`):

| 필드 | 용도 |
|---|---|
| `font`, `fontSize` | 타이핑 SVG 폰트 (Google Fonts, weight 700 지원 필요) |
| `accent.dark` / `accent.light` | 다크/라이트 모드별 타이핑 텍스트 색 |
| `badge` | 뱃지·조회수 색 (흰 글씨가 읽히는 중간 톤) |
| `gradient` | 구분선·배너 그라디언트 (2개 이상) |
| `banner` | 상·하단 캡슐 배너 모양 (`none`, `waving`, `slice`, `soft`, `cylinder`, `shark`, `rounded`, `rect` …) |
| `cards.dark` / `cards.light` | `profile-summary-card-output/` 안의 카드 테마 폴더명 |
| `icons` | skillicons 테마 (`dark` / `light`) |
| `emoji` | 섹션 헤더 이모지 |
| `snake.dark` / `snake.light` | 뱀 색과 기여도 4단계 점 색 |

## 자주 하는 작업

**오늘 이후 일정 미리보기**
```bash
python .github/theme/render.py --list 14
```

**특정 조합을 로컬에서 적용**
```bash
python .github/theme/render.py --theme dracula --layout hero
```

**GitHub에서 수동 실행** — Actions 탭 → *Daily Theme Rotation* → *Run workflow*.
`theme`, `layout` 입력을 비우면 오늘의 로테이션이 적용됩니다.

**소개·기술스택·연락처 수정** — `profile.json`만 고치면 모든 레이아웃에 반영됩니다.

**테마 추가** — `themes.json`에 객체를 하나 추가합니다. 카드 테마는 `profile-summary-card-output/`에 실제로 있는 폴더명이어야 합니다.

**레이아웃 추가** — `layouts/`에 `.md` 파일을 추가하면 자동으로 로테이션에 포함됩니다. 사용할 수 있는 토큰:

| 토큰 | 출력 |
|---|---|
| `{{typing}}` | 다크/라이트 대응 타이핑 SVG |
| `{{hero}}`, `{{hero_footer}}` | 이름이 들어간 대형 배너 / 하단 배너 |
| `{{banner_header}}`, `{{banner_footer}}` | 테마 배너 (테마가 `none`이면 빈 값) |
| `{{divider}}`, `{{divider:footer}}` | 그라디언트 구분선 |
| `{{badges:STYLE}}`, `{{connect:STYLE}}` | 위치·역할·조회수 뱃지 / 연락처 뱃지 (`for-the-badge`, `flat`, `flat-square`, `plastic`) |
| `{{quote}}`, `{{about_list}}`, `{{about_html}}`, `{{about_code}}` | 인용구 / 소개 (마크다운·HTML·코드블록) |
| `{{stack_table}}`, `{{stack_row:N}}` | 분류별 기술스택 표 / 한 줄당 N개 아이콘 묶음 |
| `{{card:NAME:WIDTH}}` | 통계 카드 (`0-profile-details`, `1-repos-per-language`, `2-most-commit-language`, `3-stats`, `4-productive-time`) |
| `{{cards_credit}}`, `{{snake}}`, `{{footer}}` | 카드 출처 / 뱀 애니메이션 / 푸터 |
| `{{e:KEY}}`, `{{theme_name}}` | 테마 이모지 (`about`, `stack`, `insights`, `graph`, `connect`) / 테마 이름 |

## 참고

- GitHub 스케줄 워크플로우는 부하가 몰리면 5~30분 정도 늦게 시작될 수 있습니다.
- `render.py`는 표준 라이브러리만 쓰므로 Python 3만 있으면 됩니다 (GitHub 러너에 기본 설치).
- 이미지 캐시 때문에 프로필 페이지에 변경이 반영되기까지 몇 분 걸릴 수 있습니다.
