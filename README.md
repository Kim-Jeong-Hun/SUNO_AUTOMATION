# Suno Studio

Windows desktop app for collecting songwriting ideas, drafting lyrics and prompts with AI, creating songs through Suno's official MCP connection, and uploading audio/video to YouTube.

## Download and build

- Download `SunoStudio.exe` from the [latest release](../../releases/latest).
- To build from source on Windows, run `build.ps1` in PowerShell. The executable is written to `dist\SunoStudio.exe`.
- The app has Korean and English interface options in **Connections & settings**.

## AI access options

Choose one of four access methods in **Connections & settings**:

| Option | What you need | Billing route |
| --- | --- | --- |
| OpenAI API | OpenAI API key | OpenAI API account |
| Claude API | Anthropic API key | Anthropic API account |
| ChatGPT subscription | Codex CLI installed and signed in to an eligible ChatGPT account | Through Codex CLI and the account's plan |
| Claude subscription | Claude Code CLI installed and signed in to an eligible Claude plan | Through Claude Code and the account's plan |

Subscription access is provided by the official CLI installed on the same computer. Suno Studio does not turn a ChatGPT or Claude subscription into an API key. API access and subscription access are separate routes, and availability depends on the provider's current plan and account policies. Install and sign in to [Codex CLI](https://developers.openai.com/codex/cli/) or [Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started) before choosing that mode.

API keys and Suno/YouTube OAuth credentials are encrypted with Windows DPAPI for the current Windows account. Existing plaintext credentials from older Suno Studio versions are migrated when the corresponding service connects. If you move app data to another Windows account or PC, saved credentials cannot be decrypted there; sign in again.

Token usage is recorded locally when the provider returns token counts. Some subscription CLI responses do not expose complete counts, so subscription totals may be incomplete. Token counts are not a price estimate; check your provider's plan and billing page.

## Create and publish a song

1. In **Idea library**, add words and concepts or ask the selected AI to suggest them.
2. In **Song studio**, set a theme, genre, and mood, then draft a title, lyrics, description, tags, and Suno prompt.
3. Connect to Suno with OAuth. The app uses Suno's official MCP endpoint; available tools can depend on Suno's beta service and your account.
4. Set up YouTube OAuth as described below. Choose the upload visibility; uploads default to **private**.
5. Start the create-and-upload flow and confirm before Suno credits are used. If Suno does not provide a downloadable audio file to the connected account, the song may remain in the Suno library without completing the upload.

You can also select an existing audio/video file and upload it. Audio-only files are wrapped in a simple title-card video for YouTube.

## YouTube OAuth setup

In Google Cloud, create a project and enable **YouTube Data API v3**. Create an OAuth client ID for a **Desktop app**, download its JSON file, name it `client_secrets.json`, and place it next to `SunoStudio.exe`. The first upload opens Google's sign-in and consent flow. Keep this file private and do not commit it to a public repository.

## Local data and privacy

- Word database, projects, and token-count history: `%APPDATA%\SunoStudio\studio.db`
- Settings: `%APPDATA%\SunoStudio\settings.json`
- Suno and YouTube OAuth credentials: `%APPDATA%\SunoStudio\`
- Personal API keys, OAuth files, and local databases are not included in this repository. API keys and OAuth credentials are encrypted for the current Windows account. Protect your Windows account and do not share the app data folder.
- Prompts and song content are sent to the AI provider selected in the app. Suno and YouTube receive the data required for their respective actions.

The app does not use unofficial Suno endpoints or browser automation. Suno's MCP beta tools and account permissions may change over time.

---

## 한국어

Suno Studio는 창작 아이디어를 모으고, AI로 가사·제목·프롬프트를 만든 뒤, Suno 공식 MCP로 곡을 제작하고 YouTube에 올리는 Windows 앱입니다.

### 다운로드 및 빌드

- [최신 릴리스](../../releases/latest)에서 `SunoStudio.exe`를 내려받으세요.
- Windows PowerShell에서 `build.ps1`을 실행하면 `dist\SunoStudio.exe`가 만들어집니다.
- **연결 및 설정**에서 한국어와 English를 선택할 수 있습니다.

### AI 이용 방식

**연결 및 설정**에서 네 가지 중 하나를 고릅니다.

| 방식 | 필요한 항목 | 결제 경로 |
| --- | --- | --- |
| OpenAI API | OpenAI API 키 | OpenAI API 계정 |
| Claude API | Anthropic API 키 | Anthropic API 계정 |
| ChatGPT 구독 | Codex CLI 설치 및 해당 ChatGPT 계정 로그인 | Codex CLI와 계정 플랜 |
| Claude 구독 | Claude Code CLI 설치 및 해당 Claude 플랜 로그인 | Claude Code와 계정 플랜 |

구독 방식은 같은 PC에 설치된 공식 CLI를 사용합니다. ChatGPT나 Claude 구독을 API 키로 바꾸는 기능은 아닙니다. API와 구독은 서로 다른 이용 경로이며, 사용 가능 여부는 각 서비스의 플랜과 계정 정책에 따라 달라집니다. 구독 방식을 고르기 전에 [Codex CLI](https://developers.openai.com/codex/cli/) 또는 [Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started)를 설치하고 로그인하세요.

앱에 입력한 API 키와 Suno/YouTube OAuth 정보는 현재 Windows 계정의 DPAPI로 암호화됩니다. 이전 버전에서 저장한 평문 인증 정보는 해당 서비스에 연결할 때 암호화 저장 방식으로 이전합니다. 앱 데이터를 다른 PC나 Windows 계정으로 옮기면 복호화할 수 없으므로 다시 로그인해야 합니다.

제공자가 토큰 수를 반환하면 앱이 로컬에 기록합니다. 구독 CLI는 토큰 수를 전부 제공하지 않을 수 있어 구독 사용량 합계가 완전하지 않을 수 있습니다. 토큰 수는 요금 계산이 아니므로 각 서비스의 플랜과 청구 내역을 확인하세요.

### 곡 만들기와 업로드

1. **아이디어 보관함**에 단어와 소재를 저장하거나 AI로 후보를 찾습니다.
2. **노래 스튜디오**에서 주제·장르·분위기를 정하고 제목·가사·설명·태그·Suno 프롬프트 초안을 만듭니다.
3. Suno 공식 MCP에 OAuth로 연결합니다. 사용할 수 있는 도구는 Suno의 베타 서비스와 계정 권한에 따라 다를 수 있습니다.
4. 아래 안내에 따라 YouTube OAuth를 설정하고 공개 범위를 고릅니다. 기본값은 **비공개**입니다.
5. 곡 생성 및 업로드를 시작하고 Suno 크레딧 사용을 확인합니다. 연결한 계정에서 오디오 파일을 내려받을 수 없으면 곡은 Suno 라이브러리에 남고 YouTube 업로드는 완료되지 않을 수 있습니다.

기존 오디오/영상 파일을 골라 업로드할 수도 있습니다. 오디오 파일은 YouTube 업로드를 위해 간단한 제목 이미지가 포함된 영상으로 변환됩니다.

### YouTube OAuth 설정

Google Cloud에서 프로젝트를 만들고 **YouTube Data API v3**를 사용 설정합니다. OAuth 클라이언트 ID를 **Desktop app** 유형으로 만들고 JSON 파일을 내려받아 `client_secrets.json`으로 이름을 바꾼 뒤 `SunoStudio.exe` 옆에 둡니다. 첫 업로드 시 Google 로그인과 권한 승인이 열립니다. 이 파일은 공개 저장소에 올리지 마세요.

### 로컬 데이터와 개인정보

- 단어 DB, 프로젝트, 토큰 수 기록: `%APPDATA%\SunoStudio\studio.db`
- 앱 설정: `%APPDATA%\SunoStudio\settings.json`
- Suno 및 YouTube OAuth 정보: `%APPDATA%\SunoStudio\`
- API 키, OAuth 파일, 로컬 DB는 저장소에 포함하지 않습니다. API 키와 OAuth 정보는 현재 Windows 계정용으로 암호화해 로컬에 저장합니다. Windows 계정을 보호하고 앱 데이터 폴더를 공유하지 마세요.
- 프롬프트와 곡 내용은 선택한 AI 제공자에게 전송됩니다. Suno와 YouTube에는 각 작업에 필요한 데이터가 전달됩니다.

비공식 Suno 엔드포인트나 브라우저 자동 조작은 사용하지 않습니다. Suno MCP 베타 도구와 계정 권한은 변경될 수 있습니다.
