import os, sys, json, sqlite3, threading, webbrowser
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP = "Suno Studio"
DATA = Path(os.getenv("APPDATA", str(Path.home()))) / "SunoStudio"
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "studio.db"

def db():
    c=sqlite3.connect(DB); c.execute("CREATE TABLE IF NOT EXISTS words(id INTEGER PRIMARY KEY, word TEXT, kind TEXT, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, model TEXT, input_tokens INTEGER, output_tokens INTEGER, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, title TEXT, lyrics TEXT, prompt TEXT, video TEXT, created TEXT)"); c.commit(); return c

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Suno Studio | 노래 제작 자동화"); self.geometry("900x720"); self.minsize(760,600)
        self.configure(bg="#111827"); self.style=ttk.Style(); self.style.theme_use("clam")
        self.style.configure("TFrame",background="#111827"); self.style.configure("TLabel",background="#111827",foreground="#e5e7eb",font=("Malgun Gothic",10))
        self.style.configure("TButton",font=("Malgun Gothic",10),padding=7); self.style.configure("TNotebook",background="#111827"); self.style.configure("TNotebook.Tab",padding=[12,7])
        self.provider=tk.StringVar(value="OpenAI"); self.api=tk.StringVar(value=os.getenv("OPENAI_API_KEY","")); self.claude_api=tk.StringVar(value=os.getenv("ANTHROPIC_API_KEY","")); self.model=tk.StringVar(value="gpt-4.1-mini"); self.genre=tk.StringVar(value="인디 팝"); self.mood=tk.StringVar(value="그리움, 따뜻함"); self.theme=tk.StringVar(value="늦은 밤 오래된 친구를 떠올리는 마음")
        self.audio=tk.StringVar(); self.privacy=tk.StringVar(value="private"); self.suno_status=tk.StringVar(value="Suno MCP 연결 전"); self._ui(); self.refresh_words(); self.refresh_usage()
    def _ui(self):
        ttk.Label(self,text="SUNO STUDIO",font=("Malgun Gothic",22,"bold")).pack(anchor="w",padx=22,pady=(18,0))
        ttk.Label(self,text="아이디어를 모으고, 노래를 만들고, 채널에 업로드하세요.").pack(anchor="w",padx=23,pady=(0,12))
        self.nb=ttk.Notebook(self); self.nb.pack(fill="both",expand=True,padx=16,pady=8)
        self.words=ttk.Frame(self.nb); self.work=ttk.Frame(self.nb); self.settings=ttk.Frame(self.nb)
        self.nb.add(self.words,text="1 · 단어 DB"); self.nb.add(self.work,text="2 · 노래 제작"); self.nb.add(self.settings,text="설정 / 사용량")
        self._words_ui(); self._work_ui(); self._settings_ui()
    def _words_ui(self):
        box=ttk.Frame(self.words); box.pack(fill="x",padx=18,pady=18)
        self.word=tk.StringVar(); self.kind=tk.StringVar(value="감정")
        ttk.Entry(box,textvariable=self.word,width=34).pack(side="left",padx=4); ttk.Combobox(box,textvariable=self.kind,values=["감정","분위기","경험","장르","이미지"],width=12,state="readonly").pack(side="left",padx=4)
        ttk.Button(box,text="단어 저장",command=self.add_word).pack(side="left",padx=4); ttk.Button(box,text="AI로 단어 탐색",command=self.discover).pack(side="left",padx=4)
        self.wordlist=tk.Listbox(self.words,bg="#1f2937",fg="white",selectbackground="#4f46e5",font=("Malgun Gothic",11),borderwidth=0); self.wordlist.pack(fill="both",expand=True,padx=22,pady=(0,14))
    def _work_ui(self):
        f=ttk.Frame(self.work); f.pack(fill="both",expand=True,padx=18,pady=14)
        for label,var in [("주제",self.theme),("장르",self.genre),("감정·분위기",self.mood)]:
            ttk.Label(f,text=label).pack(anchor="w",pady=(6,2)); ttk.Entry(f,textvariable=var).pack(fill="x")
        row=ttk.Frame(f); row.pack(fill="x",pady=10); ttk.Button(row,text="DB 단어에서 조합",command=self.combine).pack(side="left",padx=3); ttk.Button(row,text="가사·Suno 프롬프트·제목 만들기",command=self.generate).pack(side="left",padx=3)
        self.result=tk.Text(f,height=16,bg="#1f2937",fg="white",insertbackground="white",wrap="word",font=("Malgun Gothic",10),borderwidth=0); self.result.pack(fill="both",expand=True,pady=8)
        row=ttk.Frame(f); row.pack(fill="x"); ttk.Button(row,text="Suno MCP 연결",command=self.connect_suno).pack(side="left",padx=3); ttk.Button(row,text="Suno 생성 → YouTube 자동 업로드",command=self.create_suno_song).pack(side="left",padx=3); ttk.Button(row,text="Suno 열기",command=lambda:webbrowser.open("https://suno.com/create")).pack(side="left",padx=3); ttk.Button(row,text="오디오/영상 선택",command=self.pick_audio).pack(side="left",padx=3); ttk.Button(row,text="YouTube 업로드",command=self.upload).pack(side="left",padx=3)
        ttk.Label(f,textvariable=self.suno_status,wraplength=820).pack(anchor="w",pady=(6,0))
        privacy=ttk.Frame(f); privacy.pack(fill="x",pady=(4,0)); ttk.Label(privacy,text="YouTube 공개 범위:").pack(side="left",padx=(0,6)); ttk.Combobox(privacy,textvariable=self.privacy,values=["private","unlisted","public"],state="readonly",width=12).pack(side="left")
        ttk.Label(f,textvariable=self.audio).pack(anchor="w",pady=3)
    def _settings_ui(self):
        f=ttk.Frame(self.settings); f.pack(fill="both",expand=True,padx=20,pady=18)
        ttk.Label(f,text="AI 제공자").pack(anchor="w"); ttk.Combobox(f,textvariable=self.provider,values=["OpenAI","Claude"],state="readonly",width=20).pack(anchor="w",pady=5)
        ttk.Label(f,text="OpenAI API 키 (선택한 제공자가 OpenAI일 때 사용)").pack(anchor="w"); ttk.Entry(f,textvariable=self.api,show="*",width=80).pack(fill="x",pady=5)
        ttk.Label(f,text="Anthropic API 키 (선택한 제공자가 Claude일 때 사용)").pack(anchor="w"); ttk.Entry(f,textvariable=self.claude_api,show="*",width=80).pack(fill="x",pady=5)
        ttk.Label(f,text="텍스트 모델 ID (계정에서 사용할 수 있는 모델)").pack(anchor="w",pady=(8,0)); ttk.Entry(f,textvariable=self.model,width=40).pack(anchor="w",pady=5)
        ttk.Label(f,text="기본 모델: OpenAI gpt-4.1-mini / Claude claude-sonnet-5. 필요하면 유효한 모델 ID로 바꾸세요.",wraplength=780).pack(anchor="w",pady=4)
        ttk.Button(f,text="설정 저장",command=self.save_settings).pack(anchor="w",pady=8)
        self.usage_lbl=ttk.Label(f,text="호출 토큰 사용량"); self.usage_lbl.pack(anchor="w",pady=12)
        ttk.Label(f,text="Suno MCP: 노래 제작 탭에서 연결을 누르고 Suno 로그인/승인을 완료하세요. 인증 토큰은 앱 데이터 폴더에 저장됩니다.\nYouTube OAuth: 앱 폴더에 client_secrets.json을 넣어야 합니다. 첫 업로드 시 Google 로그인이 열립니다.\nDB 및 설정 위치: %s"%DATA,wraplength=780).pack(anchor="w",pady=8)
    def add_word(self):
        w=self.word.get().strip()
        if not w:return
        c=db(); c.execute("INSERT INTO words(word,kind,created) VALUES(?,?,?)",(w,self.kind.get(),datetime.now().isoformat())); c.commit(); c.close(); self.word.set(""); self.refresh_words()
    def refresh_words(self):
        if not hasattr(self,"wordlist"):return
        self.wordlist.delete(0,"end"); c=db()
        for w,k in c.execute("SELECT word,kind FROM words ORDER BY id DESC"):self.wordlist.insert("end",f"[{k}] {w}")
        c.close()
    def combine(self):
        c=db(); rows=c.execute("SELECT word,kind FROM words ORDER BY RANDOM() LIMIT 6").fetchall(); c.close()
        if rows:self.mood.set(", ".join(w for w,k in rows if k in ("감정","분위기")) or self.mood.get()); self.theme.set(self.theme.get()+" · "+", ".join(w for w,k in rows[:3]))
        else:messagebox.showinfo("단어 DB","먼저 단어를 저장하거나 AI로 탐색하세요.")
    def call_ai(self,task):
        is_claude=self.provider.get()=="Claude"; key=(self.claude_api.get() if is_claude else self.api.get()).strip()
        if not key:raise ValueError(f"설정 탭에서 {self.provider.get()} API 키를 입력하세요.")
        import urllib.request
        c=db(); vocab=c.execute("SELECT word,kind FROM words ORDER BY RANDOM() LIMIT 30").fetchall(); c.close()
        prompt=f"한국어 작사가 겸 음악 프로듀서. 아래 입력과 단어를 사용해 결과를 만들어라. JSON으로 title, lyrics, suno_prompt, description, tags 필드를 반환. lyrics는 독창적인 곡 구조([Verse], [Chorus], [Bridge])로 작성. 기존 가수/곡 모방 금지. 입력: 주제={self.theme.get()}, 장르={self.genre.get()}, 분위기={self.mood.get()}, 참고단어={vocab}, 작업={task}"
        if is_claude:
            body=json.dumps({"model":self.model.get(),"max_tokens":4096,"messages":[{"role":"user","content":prompt+"\nJSON object only."}]}).encode()
            req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        else:
            body=json.dumps({"model":self.model.get(),"input":prompt,"text":{"format":{"type":"json_object"}}}).encode()
            req=urllib.request.Request("https://api.openai.com/v1/responses",data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=90) as res: data=json.loads(res.read())
        usage=data.get("usage",{}); c=db(); c.execute("INSERT INTO usage(model,input_tokens,output_tokens,created) VALUES(?,?,?,?)",(self.model.get(),usage.get("input_tokens",0),usage.get("output_tokens",0),datetime.now().isoformat())); c.commit(); c.close(); self.refresh_usage()
        if is_claude:out="".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text")
        else:out="".join(x.get("text","") for item in data.get("output",[]) for x in item.get("content",[]) if x.get("type")=="output_text")
        if not out:raise ValueError("AI 응답에 텍스트가 없습니다.")
        return json.loads(out)
    def generate(self):
        self.result.delete("1.0","end"); self.result.insert("end","생성 중…")
        def run():
            try:
                d=self.call_ai("완성 가사와 Suno 입력용 스타일 프롬프트, 유튜브 제목/설명/태그 생성")
                self.current_data=d
                text=f"제목: {d.get('title','')}\n\nSuno 프롬프트:\n{d.get('suno_prompt','')}\n\n가사:\n{d.get('lyrics','')}\n\nYouTube 설명:\n{d.get('description','')}\n\n태그: {', '.join(d.get('tags',[]))}"
                c=db(); c.execute("INSERT INTO projects(title,lyrics,prompt,created) VALUES(?,?,?,?)",(d.get('title',''),d.get('lyrics',''),d.get('suno_prompt',''),datetime.now().isoformat())); c.commit(); c.close()
                self.after(0,lambda:(self.result.delete("1.0","end"),self.result.insert("end",text)))
            except Exception as e:self.after(0,lambda:messagebox.showerror("생성 오류",str(e)))
        threading.Thread(target=run,daemon=True).start()
    def call_ai_json(self,prompt):
        is_claude=self.provider.get()=="Claude"; key=(self.claude_api.get() if is_claude else self.api.get()).strip()
        if not key:raise ValueError(f"설정 탭에서 {self.provider.get()} API 키를 입력하세요.")
        import urllib.request
        if is_claude:
            body=json.dumps({"model":self.model.get(),"max_tokens":4096,"messages":[{"role":"user","content":prompt+"\nReturn a single JSON object only."}]}).encode()
            req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        else:
            body=json.dumps({"model":self.model.get(),"input":prompt,"text":{"format":{"type":"json_object"}}}).encode()
            req=urllib.request.Request("https://api.openai.com/v1/responses",data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=90) as res:data=json.loads(res.read())
        usage=data.get("usage",{}); c=db(); c.execute("INSERT INTO usage(model,input_tokens,output_tokens,created) VALUES(?,?,?,?)",(self.model.get(),usage.get("input_tokens",0),usage.get("output_tokens",0),datetime.now().isoformat())); c.commit(); c.close(); self.after(0,self.refresh_usage)
        if is_claude:out="".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text")
        else:out="".join(x.get("text","") for item in data.get("output",[]) for x in item.get("content",[]) if x.get("type")=="output_text")
        try:return json.loads(out)
        except json.JSONDecodeError as exc:raise ValueError("AI가 올바른 JSON 응답을 반환하지 않았습니다.") from exc
    def connect_suno(self):
        self._suno_status("Suno MCP에 연결하고 있습니다. 필요하면 브라우저에서 Suno 로그인을 승인하세요.")
        def run():
            try:
                from suno_mcp import connect_and_list_tools
                tools=connect_and_list_tools(DATA/"suno_mcp_oauth.json"); self.suno_tools=tools
                summary="\n".join(f"• {x['name']}: {x['description']}" for x in tools)
                self.after(0,lambda:(self._suno_status(f"Suno MCP 연결됨 · {len(tools)}개 도구"),self._show_suno_result("Suno MCP 도구 목록\n\n"+summary)))
            except Exception as e:self.after(0,lambda:self._suno_error(e))
        threading.Thread(target=run,daemon=True).start()
    def create_suno_song(self):
        d=getattr(self,"current_data",None)
        if not d:
            messagebox.showinfo("먼저 곡을 준비하세요","먼저 가사·Suno 프롬프트·제목 만들기를 실행하세요.");return
        if not self._youtube_setup_available():
            messagebox.showerror("YouTube 설정 필요","자동 업로드를 시작하기 전에 client_secrets.json을 EXE와 같은 폴더에 준비하거나 YouTube에 로그인해 주세요.");return
        visibility=self.privacy.get()
        if not messagebox.askyesno("생성 및 YouTube 업로드",f"Suno 생성/다운로드 크레딧을 사용할 수 있으며, 곡을 YouTube에 {visibility}으로 업로드합니다. 계속할까요?"):return
        self._suno_status("YouTube 계정을 확인한 다음 Suno 곡 생성을 시작합니다…")
        def run():
            try:
                from suno_mcp import connect_and_list_tools, invoke_tool, result_to_text
                from media_pipeline import make_youtube_video, save_audio_from_result
                yt=self._get_youtube_service()
                token_path=DATA/"suno_mcp_oauth.json"
                tools=getattr(self,"suno_tools",None) or connect_and_list_tools(token_path)
                candidates=[t for t in tools if any(k in (t["name"]+" "+t["description"]).lower() for k in ("create","generate","song","music"))]
                if not candidates:candidates=tools
                schema_text=json.dumps(candidates,ensure_ascii=False,indent=2)
                instruction=("Select the single Suno MCP tool that creates a new song (not search, edit, or analysis) and construct its arguments from its inputSchema. "
                    "Use the provided title, full lyrics, and style prompt. Return JSON {tool_name:string, arguments:object}. Do not invent schema keys. "
                    f"Song title: {d.get('title','')}\nLyrics:\n{d.get('lyrics','')}\nStyle prompt:\n{d.get('suno_prompt','')}\nAvailable tools and schemas:\n{schema_text}")
                choice=self.call_ai_json(instruction); tool_name=choice.get("tool_name"); args=choice.get("arguments")
                allowed={t["name"] for t in candidates}
                if tool_name not in allowed or not isinstance(args,dict):raise ValueError("AI가 선택한 Suno 도구/인수가 목록과 일치하지 않습니다. MCP 도구 목록을 확인하세요.")
                tool=next(t for t in candidates if t["name"]==tool_name); required=tool.get("inputSchema",{}).get("required",[])
                missing=[x for x in required if x not in args]
                if missing:raise ValueError("Suno 요청에 필수 인수가 없습니다: "+", ".join(missing))
                self.after(0,lambda:self._suno_status(f"Suno에 '{tool_name}' 생성 요청을 보냈습니다. 결과를 기다리는 중…"))
                result=invoke_tool(token_path,tool_name,args); text=result_to_text(result)
                run_dir=DATA/"runs"/datetime.now().strftime("%Y%m%d_%H%M%S"); audio_path=save_audio_from_result(result,run_dir)
                if not audio_path:
                    result,audio_path,text=self._wait_and_download_audio(token_path,tools,result,text,d,run_dir)
                if not audio_path:raise RuntimeError("Suno에서 곡은 생성했지만 자동 업로드용 오디오 파일을 가져오지 못했습니다. 다운로드 권한/월간 한도 또는 Suno MCP 도구 응답을 확인하세요. Suno 라이브러리에는 곡이 저장되어 있습니다.\n\n응답:\n"+text[:1800])
                self.after(0,lambda:self._suno_status("오디오 파일을 YouTube 영상으로 만들고 있습니다…"))
                if audio_path.suffix.lower() in (".mp4",".mov",".webm"):
                    video_path=audio_path
                else:
                    video_path=make_youtube_video(audio_path,d.get("title",self.theme.get()),self.genre.get(),run_dir/"youtube_upload.mp4")
                self.after(0,lambda:self._suno_status("제목·설명을 붙여 YouTube에 업로드하고 있습니다…"))
                video_id=self._upload_to_youtube(yt,video_path,d,lambda message:self.after(0,lambda:self._suno_status(message)))
                c=db(); c.execute("UPDATE projects SET video=? WHERE id=(SELECT MAX(id) FROM projects)",(str(video_path),)); c.commit(); c.close()
                link=f"https://youtu.be/{video_id}"; done=f"자동 업로드 완료\n\n제목: {d.get('title','')}\n공개 범위: {visibility}\n파일: {video_path}\n\n{link}\n\nSuno 응답:\n{text[:1000]}"
                self.after(0,lambda:(self._suno_status("Suno 생성부터 YouTube 업로드까지 완료했습니다."),self._show_suno_result(done),messagebox.showinfo("업로드 완료",link)))
            except Exception as e:self.after(0,lambda:self._suno_error(e))
        threading.Thread(target=run,daemon=True).start()
    def _wait_and_download_audio(self,token_path,tools,result,text,data,run_dir):
        from suno_mcp import invoke_tool,result_to_text
        from media_pipeline import save_audio_from_result
        import time
        downloaded_tools=set(); current_result=result; current_text=text
        for attempt in range(10):
            candidates=[]
            for tool in tools:
                name=tool["name"].lower(); desc=tool["description"].lower(); combined=name+" "+desc
                is_fetch=any(k in combined for k in ("download","audio","status","wait","poll","detail","result","fetch","song","music","clip"))
                forbidden=any(k in name for k in ("generate","create","edit","delete","upload","search","like","share"))
                is_download="download" in combined
                if is_fetch and not forbidden and (not is_download or tool["name"] not in downloaded_tools):candidates.append(tool)
            if not candidates:break
            schemas=json.dumps(candidates,ensure_ascii=False,indent=2)
            prompt=("Select one read-only Suno MCP status/result tool, or a download tool, to get the audio file for the song already created. "
                "Do not create another song, search, edit, delete, or upload. Return {action:'call',tool_name,arguments} or {action:'none'}. "
                f"Song title: {data.get('title','')}\nPrevious Suno response:\n{current_text[:7000]}\nTools:\n{schemas}")
            choice=self.call_ai_json(prompt); name=choice.get("tool_name"); args=choice.get("arguments")
            if choice.get("action")!="call" or name not in {t["name"] for t in candidates} or not isinstance(args,dict):break
            tool=next(t for t in candidates if t["name"]==name); missing=[x for x in tool.get("inputSchema",{}).get("required",[]) if x not in args]
            if missing:
                if "download" in name.lower():downloaded_tools.add(name)
                continue
            if "download" in name.lower():downloaded_tools.add(name)
            self.after(0,lambda n=name:self._suno_status(f"Suno '{n}' 도구로 생성 결과/오디오를 가져오는 중…"))
            current_result=invoke_tool(token_path,name,args); current_text=result_to_text(current_result)
            audio_path=save_audio_from_result(current_result,run_dir)
            if audio_path:return current_result,audio_path,current_text
            if any(word in current_text.lower() for word in ("pending","processing","generating","queued","in_progress","진행 중","생성 중")) and attempt<9:time.sleep(10)
        return current_result,None,current_text
    def _suno_status(self,text):
        self.suno_status.set(text)
    def _show_suno_result(self,text):
        self.result.delete("1.0","end"); self.result.insert("end",text)
    def _suno_error(self,error):
        self._suno_status("Suno MCP 연결/생성에 실패했습니다."); messagebox.showerror("Suno MCP 오류",str(error))
    def discover(self):
        def run():
            try:
                d=self.call_ai("창작용 단어 후보 12개를 제안. JSON {words:[{word,kind}]}로 반환. 감정/분위기/경험/장르/이미지 다양하게")
                c=db()
                for x in d.get("words",[]):c.execute("INSERT INTO words(word,kind,created) VALUES(?,?,?)",(x["word"],x.get("kind","이미지"),datetime.now().isoformat()))
                c.commit();c.close();self.after(0,self.refresh_words)
            except Exception as e:self.after(0,lambda:messagebox.showerror("탐색 오류",str(e)))
        threading.Thread(target=run,daemon=True).start()
    def pick_audio(self):
        p=filedialog.askopenfilename(filetypes=[("Audio/Video","*.mp3 *.wav *.m4a *.mp4 *.mov")])
        if p:self.audio.set(p)
    def upload(self):
        p=self.audio.get()
        if not p or not Path(p).exists():messagebox.showerror("파일 필요","Suno에서 만든 오디오 또는 영상 파일을 먼저 선택하세요.");return
        def run():
            try:
                yt=self._get_youtube_service(); media_path=Path(p)
                if media_path.suffix.lower() in (".mp3",".wav",".m4a",".aac",".flac",".ogg",".opus"):
                    from media_pipeline import make_youtube_video
                    media_path=make_youtube_video(media_path,getattr(self,"current_data",{}).get("title",self.theme.get()),self.genre.get(),DATA/"runs"/(media_path.stem+"_youtube.mp4"))
                video_id=self._upload_to_youtube(yt,media_path,getattr(self,"current_data",{})); self.after(0,lambda:messagebox.showinfo("업로드 완료",f"https://youtu.be/{video_id}"))
            except Exception as e:self.after(0,lambda:messagebox.showerror("업로드 오류",str(e)))
        threading.Thread(target=run,daemon=True).start()
    def _youtube_setup_available(self):
        if (DATA/"youtube_token.json").exists():return True
        secret=Path(sys.executable).parent/"client_secrets.json" if getattr(sys,"frozen",False) else Path(__file__).parent/"client_secrets.json"
        return secret.exists()
    def _get_youtube_service(self):
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        scope=["https://www.googleapis.com/auth/youtube.upload"]; token=DATA/"youtube_token.json"; creds=None
        if token.exists():creds=Credentials.from_authorized_user_file(str(token),scope)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:creds.refresh(Request())
            else:
                secret=Path(sys.executable).parent/"client_secrets.json" if getattr(sys,"frozen",False) else Path(__file__).parent/"client_secrets.json"
                if not secret.exists():raise FileNotFoundError("client_secrets.json을 EXE와 같은 폴더에 넣으세요.")
                creds=InstalledAppFlow.from_client_secrets_file(str(secret),scope).run_local_server(port=0)
            token.write_text(creds.to_json(),encoding="utf-8")
        return build("youtube","v3",credentials=creds)
    def _upload_to_youtube(self,yt,video_path,meta,progress=None):
        from googleapiclient.http import MediaFileUpload
        title=(meta.get("title") or self.theme.get())[:100]
        desc=(meta.get("description") or "AI 음악 프로젝트 · SUNO STUDIO")[:5000]
        raw_tags=meta.get("tags") or [self.genre.get(),"AI music","Suno"]
        if isinstance(raw_tags,str):raw_tags=[x.strip() for x in raw_tags.split(",")]
        tags=[]; total=0
        for tag in raw_tags:
            tag=str(tag).strip()[:100]
            if tag and total+len(tag)<=480:tags.append(tag); total+=len(tag)
        body={"snippet":{"title":title,"description":desc,"tags":tags,"categoryId":"10"},"status":{"privacyStatus":self.privacy.get()}}
        import mimetypes
        media_type=mimetypes.guess_type(str(video_path))[0] or "video/mp4"
        request=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video_path),mimetype=media_type,chunksize=8*1024*1024,resumable=True))
        response=None
        while response is None:
            status,response=request.next_chunk()
            if progress and status:progress(f"YouTube 업로드 중… {int(status.progress()*100)}%")
        return response["id"]
    def save_settings(self):
        (DATA/"settings.json").write_text(json.dumps({"provider":self.provider.get(),"openai_api_key":self.api.get(),"anthropic_api_key":self.claude_api.get(),"model":self.model.get()},ensure_ascii=False),encoding="utf-8")
        messagebox.showinfo("저장","설정을 저장했습니다.")
    def refresh_usage(self):
        if not hasattr(self,"usage_lbl"):return
        c=db(); a,b=c.execute("SELECT COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0) FROM usage").fetchone(); c.close(); self.usage_lbl.config(text=f"누적 OpenAI 토큰: 입력 {a:,} · 출력 {b:,} (호출별 DB 기록)")

def load_settings(app):
    p=DATA/"settings.json"
    if p.exists():
        try:
            d=json.loads(p.read_text(encoding="utf-8")); app.api.set(d.get("openai_api_key",app.api.get())); app.claude_api.set(d.get("anthropic_api_key",app.claude_api.get())); app.provider.set(d.get("provider","OpenAI")); app.model.set(d.get("model","gpt-4.1-mini"))
            if app.provider.get()=="Claude" and "model" not in d:app.model.set("claude-sonnet-5")
        except Exception:pass
if __name__=="__main__":
    app=App();load_settings(app);app.mainloop()
