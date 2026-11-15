# Suno Studio

OpenAI 또는 Claude로 한국어 가사와 Suno 프롬프트를 만들고, Suno 공식 MCP를 통해 곡 생성을 요청한 뒤 YouTube에 업로드하는 Windows 데스크톱 앱입니다.

## 실행

- GitHub Releases에서 `SunoStudio.exe`를 내려받아 실행합니다.
- 소스에서 빌드하려면 Windows PowerShell에서 `build.ps1`을 실행합니다. 결과 파일은 `dist\SunoStudio.exe`입니다.

## 처음 설정

1. **설정 / 사용량** 탭에서 OpenAI 또는 Claude를 선택하고 API 키를 입력한 다음 저장합니다. 초기 텍스트 모델은 각각 `gpt-4.1-mini`, `claude-sonnet-5`입니다.
2. **단어 DB** 탭에서 창작 단어를 직접 추가하거나 AI로 단어 후보를 만듭니다.
3. **노래 제작** 탭에서 주제, 장르, 분위기를 정하고 가사·프롬프트·제목 생성을 누릅니다.
4. Google Cloud YouTube OAuth 설정을 먼저 마칩니다(아래 참고). **Suno MCP 연결**을 눌러 브라우저에서 Suno 계정으로 로그인하고 권한을 승인합니다. 승인 토큰은 `%APPDATA%\SunoStudio\suno_mcp_oauth.json`에 저장됩니다.
5. **Suno 생성 → YouTube 자동 업로드**를 누르고 생성/다운로드와 업로드를 확인합니다. 앱은 MCP 곡 생성 도구를 호출하고, 결과의 오디오를 받기 위해 다운로드/상태 도구를 확인합니다. 오디오를 받으면 제목이 있는 정지 이미지 MP4를 만들고, 생성된 제목·설명·태그와 선택한 공개 범위로 YouTube에 업로드합니다. Suno 생성물은 라이브러리에도 저장됩니다.

Suno MCP에서 오디오 파일을 반환하지 않거나 계정에 다운로드 권한/한도가 없으면 생성물은 Suno 라이브러리에 남고 자동 업로드는 완료되지 않습니다. Suno의 다운로드 가능 여부와 월간 한도는 계정 플랜에 따라 달라집니다. 앱은 요청 전에 생성 크레딧과 YouTube 공개 범위를 확인합니다.

## YouTube 업로드 설정

Google Cloud 프로젝트에서 YouTube Data API v3를 켜고 OAuth 클라이언트 ID 유형을 데스크톱 앱으로 만든 다음, JSON 파일을 `client_secrets.json`으로 저장해 EXE와 같은 폴더에 둡니다. 첫 업로드에서 Google 로그인이 열립니다. 업로드 공개 범위는 앱에서 변경하기 전까지 비공개입니다.

## 데이터와 비용

- 로컬 SQLite DB: `%APPDATA%\SunoStudio\studio.db`
- 앱 설정: `%APPDATA%\SunoStudio\settings.json`
- Suno MCP OAuth 토큰: `%APPDATA%\SunoStudio\suno_mcp_oauth.json`
- AI API 호출별 입력/출력 토큰 수를 로컬 DB에 기록합니다. 토큰 수는 청구 비용과 같지 않으므로 각 제공자의 현재 요금표를 확인하세요.
- Suno 생성은 로그인한 Suno 계정의 크레딧을 사용합니다. 앱은 생성 요청 전에 확인 창을 띄웁니다.

Suno 연결은 공식 MCP 서버 `https://api.suno.com/mcp`와 OAuth를 사용합니다. 비공식 Suno API나 브라우저 자동 조작은 사용하지 않습니다. Suno MCP의 베타 도구 구성은 계정이나 서버 업데이트에 따라 달라질 수 있습니다.

---

## English

Suno Studio is a Windows desktop app for drafting Korean lyrics and Suno prompts with OpenAI or Claude, creating a song through Suno's official MCP server, and uploading the result to YouTube.

### Download or build

- Download **SunoStudio.exe** from the [latest GitHub Release](https://github.com/Kim-Jeong-Hun/SUNO_AUTOMATION/releases/latest).
- To build from source on Windows, run `build.ps1` in PowerShell. The executable is created at `dist\SunoStudio.exe`.
- The current app interface is in Korean; this section documents setup in English.

### Setup and first run

1. In **Settings / Usage**, choose OpenAI or Claude, enter that provider's API key, and save. The default text models are `gpt-4.1-mini` for OpenAI and `claude-sonnet-5` for Claude; you can enter another model ID supported by your account.
2. In **Word DB**, add creative words manually or ask the selected AI provider to suggest words.
3. In **Song Creation**, enter a theme, genre, and mood. Click the lyric/prompt/title button to draft Korean lyrics, a Suno style prompt, and YouTube metadata.
4. Set up YouTube OAuth as described below. Click **Connect Suno MCP** and sign in to Suno in the browser to grant access. The app stores the OAuth token in `%APPDATA%\SunoStudio\suno_mcp_oauth.json`.
5. Click **Generate on Suno → Auto-upload to YouTube** and confirm. The app calls an available Suno creation tool, checks MCP results/status/download tools for the audio, creates an MP4 with title-card artwork, and uploads it with the generated title, description, tags, and selected privacy setting. The song is also saved in your Suno library.

If Suno MCP does not return an audio file, or your account lacks download permission or remaining download allowance, the song stays in your Suno library but the automatic upload cannot finish. Suno download access and monthly limits depend on your plan. Song generation and YouTube visibility are confirmed before the workflow starts. YouTube uploads default to **private**.

### YouTube OAuth setup

In Google Cloud, create a project and enable **YouTube Data API v3**. Create an OAuth client ID with application type **Desktop app**, download its JSON file, rename it `client_secrets.json`, and place it next to `SunoStudio.exe`. The first upload opens a Google sign-in and consent page.

### Local data and costs

- SQLite word database and token usage: `%APPDATA%\SunoStudio\studio.db`
- App settings: `%APPDATA%\SunoStudio\settings.json`
- Suno MCP OAuth token: `%APPDATA%\SunoStudio\suno_mcp_oauth.json`
- YouTube OAuth token: `%APPDATA%\SunoStudio\youtube_token.json`
- API keys and OAuth tokens are stored locally by the app and are not included in this repository. The app does not encrypt these local files; protect your Windows account and do not share the files.
- AI input/output tokens are recorded per call. Token counts are not the same as billed cost; check your provider's current pricing. Suno song generation and downloads use account credits or plan allowances.

The app connects to Suno's official MCP endpoint at `https://api.suno.com/mcp` using OAuth. It does not use unofficial Suno endpoints or browser automation. The Suno MCP beta tool set may change as Suno updates the service.
