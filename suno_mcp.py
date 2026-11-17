"""OAuth-enabled client for Suno's official remote MCP server."""
import asyncio
import json
import queue
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx2
from mcp import ClientSession
from mcp.client.auth import AuthorizationCodeResult, OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from pydantic import AnyUrl
from secure_store import protect_text, unprotect_text

SERVER = "https://api.suno.com/mcp"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 41731
CALLBACK_URL = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback"


class JsonTokenStorage(TokenStorage):
    """Persist the Suno OAuth client registration and tokens between runs."""
    def __init__(self, path: Path):
        self.path = path
        self._tokens = None
        self._client_info = None
        if path.exists():
            try:
                stored = path.read_text(encoding="utf-8")
                data = json.loads(unprotect_text(stored))
                if data.get("tokens"):
                    self._tokens = OAuthToken.model_validate(data["tokens"])
                if data.get("client_info"):
                    self._client_info = OAuthClientInformationFull.model_validate(data["client_info"])
                if stored and not stored.startswith("dpapi:"):
                    self._save()
            except (ValueError, TypeError):
                pass

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tokens": self._tokens.model_dump(mode="json") if self._tokens else None,
            "client_info": self._client_info.model_dump(mode="json") if self._client_info else None,
        }
        self.path.write_text(protect_text(json.dumps(data)), encoding="utf-8")

    async def get_tokens(self):
        return self._tokens

    async def set_tokens(self, tokens):
        self._tokens = tokens
        self._save()

    async def get_client_info(self):
        return self._client_info

    async def set_client_info(self, client_info):
        self._client_info = client_info
        self._save()


class OAuthCallback:
    def __init__(self):
        self.result_queue = queue.Queue(maxsize=1)
        self.server = None
        self.thread = None

    async def open_authorization(self, auth_url: str):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                if parsed.path != "/callback":
                    self.send_error(404)
                    return
                if params.get("error"):
                    outer.result_queue.put({"error": params["error"][0]})
                    body = "Suno authorization was not completed. You may close this window."
                else:
                    outer.result_queue.put({
                        "code": params.get("code", [""])[0],
                        "state": params.get("state", [None])[0],
                        "iss": params.get("iss", [None])[0],
                    })
                    body = "Suno is connected. You may close this window and return to Suno Studio."
                data = ("<!doctype html><meta charset='utf-8'><title>Suno Studio</title><p>" + body + "</p>").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                threading.Thread(target=outer.server.shutdown, daemon=True).start()

            def log_message(self, *_):
                pass

        try:
            self.server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), Handler)
        except OSError as exc:
            raise RuntimeError(f"OAuth callback port {CALLBACK_PORT} is busy. Close the other application and retry.") from exc
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        webbrowser.open(auth_url)

    async def receive_callback(self):
        try:
            data = await asyncio.to_thread(self.result_queue.get, True, 300)
        except queue.Empty as exc:
            raise TimeoutError("Suno sign-in timed out. Click Connect and try again.") from exc
        finally:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
        if data.get("error"):
            raise RuntimeError("Suno sign-in was declined: " + data["error"])
        return AuthorizationCodeResult(code=data["code"], state=data["state"], iss=data["iss"])


def make_auth(storage, callback):
    return OAuthClientProvider(
        server_url=SERVER,
        client_metadata=OAuthClientMetadata(
            client_name="Suno Studio",
            redirect_uris=[AnyUrl(CALLBACK_URL)],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="none",
            application_type="native",
            scope="api:v0 generate_music create:generate credits:spend library:read library:write download offline_access",
        ),
        storage=storage,
        redirect_handler=callback.open_authorization,
        callback_handler=callback.receive_callback,
    )


async def _connect(token_path: Path, operation):
    storage = JsonTokenStorage(token_path)
    callback = OAuthCallback()
    auth = make_auth(storage, callback)
    async with httpx2.AsyncClient(auth=auth, timeout=httpx2.Timeout(30.0, read=300.0)) as http:
        async with streamable_http_client(SERVER, http_client=http) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await operation(session)


def connect_and_list_tools(token_path: Path):
    async def operation(session):
        result = await session.list_tools()
        return [{"name": t.name, "description": t.description or "", "inputSchema": t.inputSchema} for t in result.tools]
    return asyncio.run(_connect(token_path, operation))


def invoke_tool(token_path: Path, name: str, arguments: dict):
    async def operation(session):
        return await session.call_tool(name, arguments)
    return asyncio.run(_connect(token_path, operation))


def result_to_text(result):
    parts = []
    for item in result.content:
        if getattr(item, "type", None) == "text":
            parts.append(item.text)
        elif getattr(item, "type", None) == "image":
            parts.append("[Image result from Suno]")
        else:
            parts.append(str(item))
    if getattr(result, "structuredContent", None):
        parts.append(json.dumps(result.structuredContent, ensure_ascii=False, indent=2))
    return "\n".join(parts) or json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
