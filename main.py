import os, sys, json, sqlite3, threading, webbrowser, shutil, subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from secure_store import protect_text as protect_secret, unprotect_text as unprotect_secret

APP = "Suno Studio"
DATA = Path(os.getenv("APPDATA", str(Path.home()))) / "SunoStudio"
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "studio.db"

def is_safe_song_creation_tool(tool):
    """Restrict LLM selection to clearly named music/song creation tools."""
    import re
    name=tool.get("name","").lower()
    if any(word in name for word in ("delete","remove","edit","update","search","upload","download","share","like","publish","account","user","playlist")):return False
    action=bool(re.search(r"(^|_)(create|generate|compose)(_|$)",name))
    target=bool(re.search(r"(^|_)(song|music)(_|$)",name))
    return action and target

def db():
    c=sqlite3.connect(DB); c.execute("CREATE TABLE IF NOT EXISTS words(id INTEGER PRIMARY KEY, word TEXT, kind TEXT, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, model TEXT, input_tokens INTEGER, output_tokens INTEGER, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, title TEXT, lyrics TEXT, prompt TEXT, video TEXT, created TEXT)"); c.commit(); return c

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Suno Studio · Creative workspace"); self.geometry("1180x820"); self.minsize(980,700)
        self.colors={"bg":"#0B1020","surface":"#121A2B","raised":"#182338","field":"#0E1728","border":"#26334B","text":"#F4F6FC","muted":"#A0AEC4","accent":"#8B7CFF","accent_hover":"#7465EA","green":"#42D6A4"}
        self.configure(bg=self.colors["bg"]); self.style=ttk.Style(); self.style.theme_use("clam")
        c=self.colors; self.style.configure("TFrame",background=c["bg"]); self.style.configure("Card.TFrame",background=c["surface"]); self.style.configure("Inset.TFrame",background=c["raised"])
        self.style.configure("TLabel",background=c["bg"],foreground=c["text"],font=("Segoe UI",10)); self.style.configure("Muted.TLabel",background=c["bg"],foreground=c["muted"],font=("Segoe UI",9)); self.style.configure("Card.TLabel",background=c["surface"],foreground=c["text"],font=("Segoe UI",10)); self.style.configure("CardMuted.TLabel",background=c["surface"],foreground=c["muted"],font=("Segoe UI",9)); self.style.configure("Title.TLabel",background=c["bg"],foreground=c["text"],font=("Segoe UI Semibold",23)); self.style.configure("Section.TLabel",background=c["surface"],foreground=c["text"],font=("Segoe UI Semibold",12))
        self.style.configure("TButton",font=("Segoe UI Semibold",10),padding=(12,9),background=c["raised"],foreground=c["text"],borderwidth=0); self.style.map("TButton",background=[("active",c["border"]),("disabled",c["raised"])],foreground=[("disabled",c["muted"])])
        self.style.configure("Accent.TButton",background=c["accent"],foreground="white"); self.style.map("Accent.TButton",background=[("active",c["accent_hover"])])
        self.style.configure("TEntry",fieldbackground=c["field"],foreground=c["text"],insertcolor=c["text"],bordercolor=c["border"],lightcolor=c["border"],darkcolor=c["border"],padding=9)
        self.style.configure("TCombobox",fieldbackground=c["field"],background=c["raised"],foreground=c["text"],arrowcolor=c["muted"],padding=8); self.style.map("TCombobox",fieldbackground=[("readonly",c["field"])],foreground=[("readonly",c["text"])])
        self.style.configure("Treeview",background=c["surface"],fieldbackground=c["surface"],foreground=c["text"],borderwidth=0,rowheight=34,font=("Segoe UI",10)); self.style.configure("Treeview.Heading",background=c["raised"],foreground=c["muted"],relief="flat",font=("Segoe UI Semibold",9)); self.style.map("Treeview",background=[("selected",c["accent"])])
        self.provider=tk.StringVar(value="OpenAI API"); self.api=tk.StringVar(value=os.getenv("OPENAI_API_KEY","")); self.claude_api=tk.StringVar(value=os.getenv("ANTHROPIC_API_KEY","")); self.model=tk.StringVar(value="gpt-4.1-mini"); self.language=tk.StringVar(value="한국어"); self._saved_language="한국어"; self.genre=tk.StringVar(value="인디 팝"); self.mood=tk.StringVar(value="그리움, 따뜻함"); self.theme=tk.StringVar(value="늦은 밤 오래된 친구를 떠올리는 마음")
        self.audio=tk.StringVar(); self.privacy=tk.StringVar(value="private"); self.suno_status=tk.StringVar(value="Suno MCP 연결 전"); self.page=tk.StringVar(value="song"); self._ui(); self.refresh_words(); self.refresh_usage()
    def tr(self,ko,en): return en if self.language.get()=="English" else ko
    def _ui(self):
        for child in self.winfo_children(): child.destroy()
        root=ttk.Frame(self); root.pack(fill="both",expand=True,padx=24,pady=20)
        header=ttk.Frame(root); header.pack(fill="x",pady=(0,20)); brand=ttk.Frame(header); brand.pack(side="left")
        ttk.Label(brand,text="✦",foreground=self.colors["accent"],font=("Segoe UI",24,"bold")).pack(side="left",padx=(0,10)); ttk.Label(brand,text="SUNO STUDIO",font=("Segoe UI Semibold",17)).pack(anchor="w"); ttk.Label(brand,text=self.tr("AI 음악 제작 워크스페이스","AI music creation workspace"),style="Muted.TLabel").pack(anchor="w")
        self.top_status=ttk.Label(header,textvariable=self.suno_status,style="Muted.TLabel"); self.top_status.pack(side="right",padx=10)
        body=ttk.Frame(root); body.pack(fill="both",expand=True)
        side=ttk.Frame(body,style="Card.TFrame",width=210); side.pack(side="left",fill="y",padx=(0,18)); side.pack_propagate(False)
        ttk.Label(side,text=self.tr("작업 공간","WORKSPACE"),style="CardMuted.TLabel").pack(anchor="w",padx=18,pady=(22,10))
        self.nav={}
        for key,label in [("song",self.tr("노래 만들기","Create a song")),("words",self.tr("아이디어 보관함","Idea library")),("settings",self.tr("연결 및 설정","Connections & settings"))]:
            b=ttk.Button(side,text=label,command=lambda k=key:self.show_page(k)); b.pack(fill="x",padx=10,pady=4); self.nav[key]=b
        ttk.Frame(side,style="Card.TFrame").pack(fill="both",expand=True)
        ttk.Label(side,text=self.tr("개인 데이터는 이 PC에 저장됩니다.","Your data stays on this PC."),style="CardMuted.TLabel",wraplength=170,justify="left").pack(anchor="w",padx=18,pady=(8,18))
        self.pages=ttk.Frame(body); self.pages.pack(side="left",fill="both",expand=True)
        self.words=ttk.Frame(self.pages); self.work=ttk.Frame(self.pages); self.settings=ttk.Frame(self.pages)
        self.words.place(relwidth=1,relheight=1); self.work.place(relwidth=1,relheight=1); self.settings.place(relwidth=1,relheight=1)
        self._words_ui(); self._work_ui(); self._settings_ui(); self.show_page(self.page.get())
    def show_page(self,key):
        self.page.set(key); {"song":self.work,"words":self.words,"settings":self.settings}[key].tkraise()
        for name,button in self.nav.items(): button.configure(style="Accent.TButton" if name==key else "TButton")
        titles={"song":self.tr("노래 스튜디오","Song studio"),"words":self.tr("아이디어 보관함","Idea library"),"settings":self.tr("연결 및 설정","Connections & settings")}
        self.title("Suno Studio · "+titles[key])
    def _provider_changed(self,_event=None):
        defaults={"OpenAI API":"gpt-4.1-mini","Claude API":"claude-sonnet-5","ChatGPT subscription (Codex CLI)":"","Claude subscription (Claude Code CLI)":"sonnet"}
        self.model.set(defaults.get(self.provider.get(),""))
    def _words_ui(self):
        box=ttk.Frame(self.words); box.pack(fill="both",expand=True,padx=4,pady=4)
        ttk.Label(box,text=self.tr("아이디어 보관함","Idea library"),style="Title.TLabel").pack(anchor="w",pady=(8,3)); ttk.Label(box,text=self.tr("감정, 장소, 경험, 장르를 모아 다음 곡의 재료로 사용하세요.","Collect moods, places, memories and genres to inspire your next song."),style="Muted.TLabel").pack(anchor="w",pady=(0,20))
        card=ttk.Frame(box,style="Card.TFrame",padding=18); card.pack(fill="x",pady=(0,14)); ttk.Label(card,text=self.tr("새 아이디어","Add an idea"),style="Section.TLabel").grid(row=0,column=0,columnspan=4,sticky="w",pady=(0,12))
        self.word=tk.StringVar(); self.kind=tk.StringVar(value="감정")
        ttk.Entry(card,textvariable=self.word).grid(row=1,column=0,sticky="ew",padx=(0,8)); ttk.Combobox(card,textvariable=self.kind,values=["감정","분위기","경험","장르","이미지"],width=12,state="readonly").grid(row=1,column=1,padx=5); ttk.Button(card,text=self.tr("저장","Save"),style="Accent.TButton",command=self.add_word).grid(row=1,column=2,padx=5); ttk.Button(card,text=self.tr("AI 아이디어 찾기","Discover with AI"),command=self.discover).grid(row=1,column=3,padx=(5,0)); card.columnconfigure(0,weight=1)
        shelf=ttk.Frame(box,style="Card.TFrame",padding=16); shelf.pack(fill="both",expand=True); ttk.Label(shelf,text=self.tr("저장된 아이디어","Saved ideas"),style="Section.TLabel").pack(anchor="w",pady=(0,12))
        self.wordlist=ttk.Treeview(shelf,columns=("kind","word"),show="headings"); self.wordlist.heading("kind",text=self.tr("유형","TYPE")); self.wordlist.heading("word",text=self.tr("아이디어","IDEA")); self.wordlist.column("kind",width=130,stretch=False); self.wordlist.column("word",width=450); self.wordlist.pack(fill="both",expand=True)
    def _work_ui(self):
        f=ttk.Frame(self.work); f.pack(fill="both",expand=True,padx=4,pady=4)
        ttk.Label(f,text=self.tr("노래 스튜디오","Song studio"),style="Title.TLabel").pack(anchor="w",pady=(8,3)); ttk.Label(f,text=self.tr("아이디어를 정하고, 가사와 Suno 프롬프트를 만든 뒤 곡을 완성하세요.","Shape an idea, draft lyrics and a Suno prompt, then finish your release."),style="Muted.TLabel").pack(anchor="w",pady=(0,18))
        card=ttk.Frame(f,style="Card.TFrame",padding=18); card.pack(fill="x"); ttk.Label(card,text=self.tr("곡의 방향","SONG DIRECTION"),style="Section.TLabel").grid(row=0,column=0,columnspan=3,sticky="w",pady=(0,12))
        for col,(label,var,en_label) in enumerate([("주제",self.theme,"Theme"),("장르",self.genre,"Genre"),("감정·분위기",self.mood,"Mood")]):
            ttk.Label(card,text=self.tr(label,en_label),style="CardMuted.TLabel").grid(row=1,column=col,sticky="w",padx=(0,12)); ttk.Entry(card,textvariable=var).grid(row=2,column=col,sticky="ew",padx=(0,12),pady=(5,0)); card.columnconfigure(col,weight=1)
        actions=ttk.Frame(f); actions.pack(fill="x",pady=12); ttk.Button(actions,text=self.tr("아이디어 섞기","Mix ideas"),command=self.combine).pack(side="left",padx=(0,8)); ttk.Button(actions,text=self.tr("가사 · 제목 · 프롬프트 만들기","Draft lyrics · title · prompt"),style="Accent.TButton",command=self.generate).pack(side="left")
        output=ttk.Frame(f,style="Card.TFrame",padding=12); output.pack(fill="both",expand=True); ttk.Label(output,text=self.tr("초안","DRAFT"),style="Section.TLabel").pack(anchor="w",pady=(0,8)); self.result=tk.Text(output,height=12,bg=self.colors["field"],fg=self.colors["text"],insertbackground="white",selectbackground=self.colors["accent"],wrap="word",font=("Segoe UI",10),borderwidth=0,relief="flat",padx=12,pady=12); self.result.pack(fill="both",expand=True)
        row=ttk.Frame(f); row.pack(fill="x",pady=(12,0)); ttk.Button(row,text=self.tr("Suno 연결","Connect Suno"),command=self.connect_suno).pack(side="left",padx=(0,6)); ttk.Button(row,text=self.tr("Suno 생성 + YouTube 업로드","Create on Suno + upload"),style="Accent.TButton",command=self.create_suno_song).pack(side="left",padx=6); ttk.Button(row,text=self.tr("파일 선택 후 업로드","Choose file + upload"),command=self.pick_audio).pack(side="left",padx=6)
        privacy=ttk.Frame(f); privacy.pack(fill="x",pady=(9,0)); ttk.Label(privacy,text=self.tr("업로드 공개 범위","Upload visibility"),style="Muted.TLabel").pack(side="left",padx=(0,8)); ttk.Combobox(privacy,textvariable=self.privacy,values=["private","unlisted","public"],state="readonly",width=12).pack(side="left"); ttk.Label(privacy,textvariable=self.audio,style="Muted.TLabel").pack(side="left",padx=12)
    def _settings_ui(self):
        f=ttk.Frame(self.settings); f.pack(fill="both",expand=True,padx=4,pady=4); ttk.Label(f,text=self.tr("연결 및 설정","Connections & settings"),style="Title.TLabel").pack(anchor="w",pady=(8,3)); ttk.Label(f,text=self.tr("원하는 결제 경로를 선택하고, 연결 정보를 안전하게 관리하세요.","Choose your billing route and manage connections."),style="Muted.TLabel").pack(anchor="w",pady=(0,18))
        ai=ttk.Frame(f,style="Card.TFrame",padding=18); ai.pack(fill="x",pady=(0,12)); ttk.Label(ai,text=self.tr("AI 제공자 및 결제 방식","AI provider & billing"),style="Section.TLabel").pack(anchor="w",pady=(0,12))
        ttk.Label(ai,text=self.tr("사용 방식","ACCESS METHOD"),style="CardMuted.TLabel").pack(anchor="w"); self.mode_combo=ttk.Combobox(ai,textvariable=self.provider,values=["OpenAI API","Claude API","ChatGPT subscription (Codex CLI)","Claude subscription (Claude Code CLI)"],state="readonly",width=54); self.mode_combo.pack(anchor="w",pady=(5,12)); self.mode_combo.bind("<<ComboboxSelected>>",self._provider_changed); ttk.Label(ai,text=self.tr("OpenAI API 키","OPENAI API KEY"),style="CardMuted.TLabel").pack(anchor="w"); ttk.Entry(ai,textvariable=self.api,show="*").pack(fill="x",pady=(5,12)); ttk.Label(ai,text=self.tr("Anthropic API 키","ANTHROPIC API KEY"),style="CardMuted.TLabel").pack(anchor="w"); ttk.Entry(ai,textvariable=self.claude_api,show="*").pack(fill="x",pady=(5,12)); ttk.Label(ai,text=self.tr("텍스트 모델 ID","TEXT MODEL ID"),style="CardMuted.TLabel").pack(anchor="w"); ttk.Entry(ai,textvariable=self.model).pack(fill="x",pady=(5,0))
        ttk.Label(ai,text=self.tr("구독 방식은 PC에 로그인된 공식 Codex CLI 또는 Claude Code CLI를 사용합니다. 토큰 카운트는 구독 플랜 청구액과 다를 수 있습니다.","Subscription modes use the official Codex CLI or Claude Code CLI signed in on this PC. Token counts may differ from plan billing."),style="CardMuted.TLabel",wraplength=720).pack(anchor="w",pady=(12,0))
        local=ttk.Frame(f,style="Card.TFrame",padding=18); local.pack(fill="x",pady=(0,12)); ttk.Label(local,text=self.tr("앱 설정","APP PREFERENCES"),style="Section.TLabel").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,10)); ttk.Label(local,text=self.tr("언어 / Language","LANGUAGE"),style="CardMuted.TLabel").grid(row=1,column=0,sticky="w"); ttk.Combobox(local,textvariable=self.language,values=["한국어","English"],state="readonly",width=18).grid(row=1,column=1,sticky="w",padx=12); ttk.Button(local,text=self.tr("설정 저장","Save settings"),style="Accent.TButton",command=self.save_settings).grid(row=1,column=2,sticky="e"); local.columnconfigure(0,weight=1)
        self.usage_lbl=ttk.Label(local,text=self.tr("토큰 사용량","Token usage"),style="CardMuted.TLabel"); self.usage_lbl.grid(row=2,column=0,columnspan=3,sticky="w",pady=(14,0)); ttk.Label(local,text=self.tr("Suno는 노래 화면에서 연결하세요. YouTube는 앱 옆 client_secrets.json과 Google 로그인이 필요합니다.","Connect Suno from Song studio. YouTube needs client_secrets.json beside the app and Google sign-in."),style="CardMuted.TLabel",wraplength=760,justify="left").grid(row=3,column=0,columnspan=3,sticky="w",pady=(10,0))
    def add_word(self):
        w=self.word.get().strip()
        if not w:return
        c=db(); c.execute("INSERT INTO words(word,kind,created) VALUES(?,?,?)",(w,self.kind.get(),datetime.now().isoformat())); c.commit(); c.close(); self.word.set(""); self.refresh_words()
    def refresh_words(self):
        if not hasattr(self,"wordlist"):return
        self.wordlist.delete(*self.wordlist.get_children()); c=db()
        for w,k in c.execute("SELECT word,kind FROM words ORDER BY id DESC"):self.wordlist.insert("","end",values=(k,w))
        c.close()
    def combine(self):
        c=db(); rows=c.execute("SELECT word,kind FROM words ORDER BY RANDOM() LIMIT 6").fetchall(); c.close()
        if rows:self.mood.set(", ".join(w for w,k in rows if k in ("감정","분위기")) or self.mood.get()); self.theme.set(self.theme.get()+" · "+", ".join(w for w,k in rows[:3]))
        else:messagebox.showinfo("단어 DB","먼저 단어를 저장하거나 AI로 탐색하세요.")
    def call_ai(self,task):
        c=db(); vocab=c.execute("SELECT word,kind FROM words ORDER BY RANDOM() LIMIT 30").fetchall(); c.close()
        prompt=f"You are an original music producer and lyricist. Reply in {self.language.get()} and do not imitate existing artists or songs. Return one JSON object with title, lyrics, suno_prompt, description, tags. Use [Verse], [Chorus], [Bridge] sections. Theme={self.theme.get()}, genre={self.genre.get()}, mood={self.mood.get()}, reference words={vocab}, task={task}. JSON only."
        return self._request_ai(prompt)
    def generate(self):
        self.result.delete("1.0","end"); self.result.insert("end","생성 중…")
        def run():
            try:
                d=self.call_ai("완성 가사와 Suno 입력용 스타일 프롬프트, 유튜브 제목/설명/태그 생성")
                self.current_data=d
                if self.language.get()=="English":text=f"Title: {d.get('title','')}\n\nSuno prompt:\n{d.get('suno_prompt','')}\n\nLyrics:\n{d.get('lyrics','')}\n\nYouTube description:\n{d.get('description','')}\n\nTags: {', '.join(d.get('tags',[]))}"
                else:text=f"제목: {d.get('title','')}\n\nSuno 프롬프트:\n{d.get('suno_prompt','')}\n\n가사:\n{d.get('lyrics','')}\n\nYouTube 설명:\n{d.get('description','')}\n\n태그: {', '.join(d.get('tags',[]))}"
                c=db(); c.execute("INSERT INTO projects(title,lyrics,prompt,created) VALUES(?,?,?,?)",(d.get('title',''),d.get('lyrics',''),d.get('suno_prompt',''),datetime.now().isoformat())); c.commit(); c.close()
                self.after(0,lambda:(self.result.delete("1.0","end"),self.result.insert("end",text)))
            except Exception as e:self.after(0,lambda:messagebox.showerror("생성 오류",str(e)))
        threading.Thread(target=run,daemon=True).start()
    def call_ai_json(self,prompt):
        return self._request_ai(prompt+"\nReturn a single JSON object only.")
    def _request_ai(self,prompt):
        mode=self.provider.get(); is_claude=mode.startswith("Claude"); is_subscription="subscription" in mode
        if is_subscription:
            out,usage_in,usage_out=self._subscription_request(prompt,mode)
        else:
            key=(self.claude_api.get() if is_claude else self.api.get()).strip()
            if not key:raise ValueError(f"설정에서 {mode}를 선택하고 해당 API 키를 입력하세요.")
            out,usage_in,usage_out=self._api_request(prompt,is_claude,key)
        c=db(); c.execute("INSERT INTO usage(model,input_tokens,output_tokens,created) VALUES(?,?,?,?)",(self.model.get() or mode,usage_in,usage_out,datetime.now().isoformat())); c.commit(); c.close(); self.after(0,self.refresh_usage)
        if not out:raise ValueError("AI 응답에 텍스트가 없습니다.")
        try:return json.loads(out)
        except json.JSONDecodeError:
            import re
            match=re.search(r"\{.*\}",out,re.S)
            if match:
                try:return json.loads(match.group(0))
                except json.JSONDecodeError:pass
            raise ValueError("AI가 올바른 JSON 응답을 반환하지 않았습니다. 모델 응답 형식을 확인하세요.")
    def _api_request(self,prompt,is_claude,key):
        import urllib.request
        if is_claude:
            body=json.dumps({"model":self.model.get() or "claude-sonnet-5","max_tokens":4096,"messages":[{"role":"user","content":prompt}]}).encode()
            req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        else:
            body=json.dumps({"model":self.model.get() or "gpt-4.1-mini","input":prompt,"text":{"format":{"type":"json_object"}}}).encode()
            req=urllib.request.Request("https://api.openai.com/v1/responses",data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=120) as res:data=json.loads(res.read())
        except Exception as exc:
            detail=getattr(exc,"read",lambda:b"")()
            raise RuntimeError(f"{('Anthropic' if is_claude else 'OpenAI')} API 요청 실패: {detail.decode('utf-8','replace')[:700] or exc}") from exc
        usage=data.get("usage",{})
        if is_claude:out="".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text")
        else:out="".join(x.get("text","") for item in data.get("output",[]) for x in item.get("content",[]) if x.get("type")=="output_text")
        return out,usage.get("input_tokens",0),usage.get("output_tokens",0)
    def _subscription_request(self,prompt,mode):
        if mode.startswith("ChatGPT"):
            codex=shutil.which("codex.cmd") or shutil.which("codex")
            if not codex:raise FileNotFoundError("ChatGPT 구독 모드를 사용하려면 Codex CLI를 설치하고 로그인하세요: https://developers.openai.com/codex/cli/")
            if codex.lower().endswith((".cmd",".bat")):
                command=[os.environ.get("COMSPEC","cmd.exe"),"/d","/s","/c",f'""{codex}" exec --json --ephemeral --sandbox read-only --skip-git-repo-check -"']
            else:command=[codex,"exec","--json","--ephemeral","--sandbox","read-only","--skip-git-repo-check","-"]
            result=subprocess.run(command,input=prompt,text=True,capture_output=True,timeout=240,encoding="utf-8",errors="replace",cwd=str(DATA))
            if result.returncode:raise RuntimeError("Codex CLI 요청 실패. Codex CLI에서 ChatGPT 계정으로 로그인했는지 확인하세요.\n"+result.stderr[-1000:])
            out=""; usage_in=usage_out=0
            for line in result.stdout.splitlines():
                try:event=json.loads(line)
                except json.JSONDecodeError:continue
                if event.get("type")=="item.completed" and event.get("item",{}).get("type")=="agent_message":out=event["item"].get("text",out)
                if event.get("type")=="turn.completed":usage_in=event.get("usage",{}).get("input_tokens",0); usage_out=event.get("usage",{}).get("output_tokens",0)
            if not out:out=result.stdout.strip()
            return out,usage_in,usage_out
        claude=shutil.which("claude")
        if not claude:raise FileNotFoundError("Claude 구독 모드를 사용하려면 Claude Code를 설치하고 로그인하세요: https://code.claude.com/docs/en/overview")
        command=[claude,"-p","--output-format","json","--no-session-persistence","--model",self.model.get() or "sonnet","--tools",""]
        result=subprocess.run(command,input=prompt,text=True,capture_output=True,timeout=240,encoding="utf-8",errors="replace",cwd=str(DATA))
        if result.returncode:raise RuntimeError("Claude Code 요청 실패. Claude Code에서 Claude 계정으로 로그인했는지 확인하세요.\n"+result.stderr[-1000:])
        try:data=json.loads(result.stdout)
        except json.JSONDecodeError:return result.stdout.strip(),0,0
        return data.get("result", ""),data.get("usage",{}).get("input_tokens",0),data.get("usage",{}).get("output_tokens",0)
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
                candidates=[t for t in tools if is_safe_song_creation_tool(t)]
                if not candidates:raise RuntimeError("Suno MCP 도구 중 이름이 명확한 곡 생성 도구를 찾지 못했습니다. 도구 목록을 확인하세요.")
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
                allowed_args=set(tool.get("inputSchema",{}).get("properties",{}))
                unexpected=set(args)-allowed_args
                if unexpected:raise ValueError("Suno 요청에 스키마에 없는 인수가 포함되어 있습니다: "+", ".join(sorted(unexpected)))
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
        if token.exists():
            token_data=unprotect_secret(token.read_text(encoding="utf-8"))
            creds=Credentials.from_authorized_user_info(json.loads(token_data),scope)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:creds.refresh(Request())
            else:
                secret=Path(sys.executable).parent/"client_secrets.json" if getattr(sys,"frozen",False) else Path(__file__).parent/"client_secrets.json"
                if not secret.exists():raise FileNotFoundError("client_secrets.json을 EXE와 같은 폴더에 넣으세요.")
                creds=InstalledAppFlow.from_client_secrets_file(str(secret),scope).run_local_server(port=0)
        token.write_text(protect_secret(creds.to_json()),encoding="utf-8")
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
    def save_settings(self,silent=False):
        (DATA/"settings.json").write_text(json.dumps({"provider":self.provider.get(),"openai_api_key":protect_secret(self.api.get()),"anthropic_api_key":protect_secret(self.claude_api.get()),"model":self.model.get(),"language":self.language.get()},ensure_ascii=False),encoding="utf-8")
        if getattr(self,"_saved_language",self.language.get())!=self.language.get():self._saved_language=self.language.get(); self._ui(); self.refresh_words(); self.refresh_usage()
        if not silent:messagebox.showinfo(self.tr("설정","Settings"),self.tr("설정을 저장했습니다.","Settings saved."))
    def refresh_usage(self):
        if not hasattr(self,"usage_lbl"):return
        c=db(); a,b=c.execute("SELECT COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0) FROM usage").fetchone(); c.close(); self.usage_lbl.config(text=self.tr(f"누적 토큰: 입력 {a:,} · 출력 {b:,} (호출별 기록)",f"Total tokens: input {a:,} · output {b:,} (logged per call)"))

def load_settings(app):
    p=DATA/"settings.json"
    if p.exists():
        try:
            d=json.loads(p.read_text(encoding="utf-8")); old_openai=d.get("openai_api_key",""); old_claude=d.get("anthropic_api_key",""); app.api.set(unprotect_secret(old_openai) or app.api.get()); app.claude_api.set(unprotect_secret(old_claude) or app.claude_api.get()); app.provider.set(d.get("provider","OpenAI API")); app.model.set(d.get("model","gpt-4.1-mini")); app.language.set(d.get("language","한국어")); app._saved_language=app.language.get()
            if app.provider.get()=="Claude":app.provider.set("Claude API")
            if app.provider.get()=="OpenAI":app.provider.set("OpenAI API")
            if (old_openai and not old_openai.startswith("dpapi:")) or (old_claude and not old_claude.startswith("dpapi:")):app.save_settings(silent=True)
        except Exception:pass
if __name__=="__main__":
    app=App();load_settings(app);app._ui();app.refresh_words();app.refresh_usage();app.mainloop()
