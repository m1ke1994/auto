"""Local-account diagnostic. No token, signed URL or model archive is exported."""
import io
import json
import os
import re
import socket
import time
import zipfile
from urllib.parse import urlsplit
import requests

API = "https://api.sketchfab.com/v3"
MAX_ARCHIVE = 16 * 1024 * 1024
CDN = {"sketchfab-prod-media.s3.amazonaws.com"}
UID = re.compile(r"[0-9a-f]{32}")

def request_bytes(url, *, headers=None, params=None, limit=1024*1024, timeout=(8,30)):
    try:
        with requests.get(url, headers=headers, params=params, stream=True,
                          timeout=timeout, allow_redirects=False) as response:
            status = response.status_code
            if status != 200:
                raise ValueError("HTTP " + str(status))
            data = bytearray()
            for part in response.iter_content(65536):
                if len(data)+len(part)>limit:
                    raise ValueError("response exceeds configured limit")
                data.extend(part)
            return bytes(data)
    except requests.RequestException as exc:
        # Do not print the exception text: it can contain a signed URL.
        host=urlsplit(url).hostname or "unknown"
        raise NetworkFailure("network request failed: "+type(exc).__name__+"; host="+host) from None

class NetworkFailure(ValueError):
    pass

def cdn_diagnostics(host):
    # No URL query, credentials or response body is logged.
    try:
        socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        print("SKETCHFAB_CDN_DNS_OK",flush=True)
    except OSError as exc:
        print("SKETCHFAB_CDN_DNS_FAILED: "+type(exc).__name__,flush=True)
        return
    try:
        with socket.create_connection((host,443),timeout=8):
            print("SKETCHFAB_CDN_TCP_OK",flush=True)
    except OSError as exc:
        print("SKETCHFAB_CDN_TCP_FAILED: "+type(exc).__name__,flush=True)
    print("SKETCHFAB_HTTPS_PROXY_CONFIGURED: "+str(bool(requests.utils.get_environ_proxies("https://"+host).get("https"))),flush=True)

def api(path, token, params=None):
    # GET requests are bounded and retried only on transient transport errors.
    # Never log the token, query parameters or signed CDN URL.
    stage = ("search" if path == "/search" else "auth" if path == "/me"
             else "download-link" if path.endswith("/download") else "model-detail")
    for attempt in range(1,3):
        try:
            print("SKETCHFAB_API: "+stage+"; attempt="+str(attempt)+"/2",flush=True)
            data=request_bytes(API+path,headers={"Authorization":"Token "+token},
                               params=params,timeout=(12,45))
            return json.loads(data)
        except NetworkFailure as exc:
            print("SKETCHFAB_API_ERROR: "+stage+"; "+str(exc),flush=True)
            if attempt==2:
                raise NetworkFailure("Sketchfab "+stage+" failed after two attempts: "+str(exc)) from None
            time.sleep(2)
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError("invalid JSON response") from None

def license_ok(item):
    license = item.get("license")
    if not isinstance(license,dict):
        return False
    return license.get("slug") in ("cc0","by") or license.get("url") in (
        "https://creativecommons.org/publicdomain/zero/1.0/",
        "http://creativecommons.org/publicdomain/zero/1.0/",
        "https://creativecommons.org/licenses/by/4.0/",
        "http://creativecommons.org/licenses/by/4.0/")

def allowed_cdn(url):
    if not isinstance(url,str):
        return False
    try:
        p=urlsplit(url)
        return p.scheme=="https" and p.netloc.lower() in CDN and p.path.startswith("/archives/")
    except ValueError:
        return False

def validate_archive(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist()
            if len(entries)>100 or sum(x.file_size for x in entries)>48*1024*1024:
                raise ValueError("archive exceeds unpacked size limit")
            scenes=[x for x in entries if x.filename.lower().endswith(".gltf")]
            if len(scenes)!=1 or scenes[0].file_size>2*1024*1024:
                raise ValueError("expected one glTF scene")
            scene=json.loads(archive.read(scenes[0]))
            if scene.get("asset",{}).get("version")!="2.0" or not scene.get("meshes"):
                raise ValueError("not a glTF 2.0 mesh")
    except (zipfile.BadZipFile,RuntimeError,UnicodeError,json.JSONDecodeError,AttributeError,NotImplementedError):
        raise ValueError("invalid glTF archive") from None

def probe(token):
    if not token.strip() or any(c.isspace() for c in token):
        raise ValueError("Set SKETCHFAB_API_TOKEN in .env.studio.local")
    try:
        me=api("/me",token)
        if not isinstance(me,dict) or not me.get("uid"):
            raise ValueError("unexpected account response")
    except ValueError as exc:
        raise ValueError("SKETCHFAB_AUTH_FAILED: "+str(exc)) from None
    print("SKETCHFAB_AUTH_OK",flush=True)
    data=api("/search",token,{"type":"models","q":"chair","downloadable":"true","count":24})
    candidates=[]
    for item in data.get("results",[]):
        uid=item.get("uid","")
        if not isinstance(uid,str) or not UID.fullmatch(uid):
            continue
        if item.get("isDownloadable") is False:
            continue
        faces=item.get("faceCount")
        if type(faces) is int and faces>100000:
            continue
        # Search may omit license metadata, so verify on the model detail endpoint.
        candidates.append((faces if type(faces) is int else 100000,uid))
    selected=None
    for _,uid in sorted(candidates)[:8]:
        detail=api("/models/"+uid,token)
        if detail.get("isDownloadable") is True and license_ok(detail):
            selected=uid
            break
    if not selected:
        raise ValueError("SKETCHFAB_SEARCH_OK: no verified CC0/CC BY downloadable candidate; try another search later")
    print("SKETCHFAB_SEARCH_OK: model="+selected,flush=True)
    for attempt in range(1,3):
        try:
            result=api("/models/"+selected+"/download",token)
        except ValueError as exc:
            raise ValueError("SKETCHFAB_DOWNLOAD_FAILED: "+str(exc)) from None
        entry=result.get("gltf",{})
        url=entry.get("url")
        if not allowed_cdn(url):
            raise ValueError("SKETCHFAB_LINK_UNSUPPORTED: absent or unapproved CDN address")
        print("SKETCHFAB_DOWNLOAD_LINK_OK",flush=True)
        size=entry.get("size")
        if type(size) is int and size>MAX_ARCHIVE:
            raise ValueError("SKETCHFAB_ARCHIVE_TOO_LARGE: link works, test limit is 16 MiB")
        host=urlsplit(url).hostname
        print("SKETCHFAB_CDN_ATTEMPT: "+str(attempt)+"/2; host="+host,flush=True)
        try:
            raw=request_bytes(url,limit=MAX_ARCHIVE,timeout=(15,90))
            break
        except NetworkFailure as exc:
            print("SKETCHFAB_CDN_ERROR: "+str(exc),flush=True)
            if attempt==2:
                cdn_diagnostics(host)
                raise ValueError("SKETCHFAB_CDN_DOWNLOAD_FAILED") from None
            time.sleep(2)
    validate_archive(raw)
    print("SKETCHFAB_OK: glTF archive downloaded and validated; bytes="+str(len(raw)),flush=True)

if __name__=="__main__":
    try:
        probe(os.environ.get("SKETCHFAB_API_TOKEN","").strip())
    except ValueError as exc:
        print(str(exc),flush=True)
        raise SystemExit(1) from None
