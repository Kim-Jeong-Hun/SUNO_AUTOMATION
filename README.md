# Suno Studio

OpenAI 또는 Claude로 한국어 가사와 Suno 프롬프트를 만들고, Suno 공식 MCP를 통해 곡 생성을 요청한 뒤 YouTube에 업로드하는 Windows 데스크톱 앱입니다.

## 실행

- GitHub Releases에서 `SunoStudio.exe`를 내려받아 실행합니다.
- 소스에서 빌드하려면 Windows PowerShell에서 `build.ps1`을 실행합니다. 결과 파일은 `dist\SunoStudio.exe`입니다.

## 처음 설정

1. **설정 / 사용량** 탭에서 OpenAI 또는 Claude를 선택하고 API 키를 입력한 다음 저장합니다. 초기 텍스트 모델은 각각 `gpt-4.1-mini`, `claude-sonnet-5`입니다.
2. **단어 DB** 탭에서 창작 단어를 직접 추가하거나 AI로 단어 후보를 만듭니다.
3. **노래 제작** 탭에서 주제, 장르, 분위기를 정하고 가사·프롬프트·제목 생성을 누릅니다.
4. **Suno MCP 연결**을 눌러 브라우저에서 Suno 계정으로 로그인하고 권한을 승인합니다. 승인 토큰은 `%APPDATA%\SunoStudio\suno_mcp_oauth.json`에 저장됩니다.
5. **Suno에서 노래 생성**을 누르고 크레딧 사용을 확인합니다. 앱은 연결된 MCP 도구를 확인하고, 가사·제목·스타일 프롬프트에 맞는 곡 생성 도구를 호출합니다. 결과는 Suno 라이브러리에 저장됩니다.
6. 생성된 오디오를 다운로드한 후 앱에서 파일을 선택하고 YouTube 업로드를 누릅니다.

## YouTube 업로드 설정

Google Cloud 프로젝트에서 YouTube Data API v3를 켜고 OAuth 클라이언트 ID 유형을 데스크톱 앱으로 만든 다음, JSON 파일을 `client_secrets.json`으로 저장해 EXE와 같은 폴더에 둡니다. 첫 업로드에서 Google 로그인이 열립니다. 업로드 공개 범위는 앱에서 변경하기 전까지 비공개입니다.

## 데이터와 비용

- 로컬 SQLite DB: `%APPDATA%\SunoStudio\studio.db`
- 앱 설정: `%APPDATA%\SunoStudio\settings.json`
- Suno MCP OAuth 토큰: `%APPDATA%\SunoStudio\suno_mcp_oauth.json`
- AI API 호출별 입력/출력 토큰 수를 로컬 DB에 기록합니다. 토큰 수는 청구 비용과 같지 않으므로 각 제공자의 현재 요금표를 확인하세요.
- Suno 생성은 로그인한 Suno 계정의 크레딧을 사용합니다. 앱은 생성 요청 전에 확인 창을 띄웁니다.

Suno 연결은 공식 MCP 서버 `https://api.suno.com/mcp`와 OAuth를 사용합니다. 비공식 Suno API나 브라우저 자동 조작은 사용하지 않습니다. Suno MCP의 베타 도구 구성은 계정이나 서버 업데이트에 따라 달라질 수 있습니다.
