"""Bounded Pexels photo retrieval. No user-supplied download URLs or secret output."""
import io
import json
from urllib.parse import urlsplit
import requests
from PIL import Image, ImageOps

MAX_SEARCHES = 5
MAX_PHOTOS = 6
MAX_DOWNLOAD = 12 * 1024 * 1024
MAX_OUTPUT = 2 * 1024 * 1024

def allowed_url(value, hosts):
    if not isinstance(value,str):
        return False
    try:
        u = urlsplit(value)
        return (u.scheme == "https" and u.netloc.lower() in hosts
                and not u.username and not u.password and bool(u.path))
    except ValueError:
        return False

def short_text(value, limit=200):
    return value.strip()[:limit] if isinstance(value,str) else ""

class MediaLibrary:
    def __init__(self, key):
        self._key = key.strip()
        self.searches = 0
        self.downloads = 0
        self.candidates = {}
        self.assets = {}
        self.credits = {}

    @property
    def enabled(self):
        return bool(self._key)

    def search(self, query, orientation="landscape"):
        if not self.enabled:
            raise ValueError("Pexels is not configured. Use procedural illustrations.")
        if not 3 <= len(query.strip()) <= 160 or orientation not in ("landscape","portrait","square"):
            raise ValueError("Use a 3-160 character photo query and landscape, portrait or square.")
        if self.searches >= MAX_SEARCHES:
            raise ValueError("Photo search limit reached.")
        self.searches += 1
        try:
            with requests.get("https://api.pexels.com/v1/search",
                headers={"Authorization":self._key},
                params={"query":query.strip(),"orientation":orientation,"per_page":6},
                timeout=(8,20),allow_redirects=False,stream=True) as response:
                if response.status_code != 200:
                    raise ValueError("Pexels search HTTP " + str(response.status_code))
                data = json.loads(self._bounded_bytes(response,256*1024))
            result = []
            for photo in data.get("photos",[])[:6]:
                pid = photo.get("id")
                if type(pid) is not int or not 0 < pid < 10**15:
                    continue
                src = photo.get("src",{}).get("large2x")
                page = photo.get("url")
                if not allowed_url(src,{"images.pexels.com"}) or not allowed_url(page,{"www.pexels.com","pexels.com"}):
                    continue
                self.candidates[pid] = {"id":pid,"photographer":short_text(photo.get("photographer"),120),
                    "alt":short_text(photo.get("alt")),"url":page,"download":src,
                    "width":photo.get("width"),"height":photo.get("height")}
                result.append({k:v for k,v in self.candidates[pid].items() if k != "download"})
            return result
        except (requests.RequestException, KeyError, TypeError, AttributeError, json.JSONDecodeError):
            raise ValueError("Pexels search failed; check connectivity or quota.") from None

    @staticmethod
    def _bounded_bytes(response,limit):
        buf=bytearray()
        for chunk in response.iter_content(64*1024):
            if len(buf)+len(chunk)>limit:
                raise ValueError("Pexels response exceeds size limit.")
            buf.extend(chunk)
        return bytes(buf)

    def save(self, photo_id):
        if type(photo_id) is not int or photo_id not in self.candidates:
            raise ValueError("Choose a photo id from the current Pexels search.")
        path=f"src/media/pexels-{photo_id}.webp"
        if path in self.assets:
            return self.credits[path]
        if self.downloads >= MAX_PHOTOS:
            raise ValueError("Photo download limit reached.")
        self.downloads += 1
        item=self.candidates[photo_id]
        try:
            # No API key on CDN requests; no redirects, only a vetted CDN URL.
            with requests.get(item["download"],timeout=(8,30),allow_redirects=False,stream=True) as response:
                if response.status_code != 200:
                    raise ValueError("Pexels image HTTP "+str(response.status_code))
                raw=self._bounded_bytes(response,MAX_DOWNLOAD)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ("JPEG","PNG","WEBP") or source.width*source.height>25_000_000:
                    raise ValueError("Unsupported or oversized photo.")
                image=ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((1920,1920),Image.Resampling.LANCZOS)
                out=io.BytesIO()
                image.save(out,"WEBP",quality=82,method=4)
                data=out.getvalue()
            if not data or len(data)>MAX_OUTPUT:
                raise ValueError("Optimized photo exceeds size limit.")
        except (requests.RequestException,OSError,Image.DecompressionBombError):
            raise ValueError("Pexels image download or decoding failed.") from None
        credit={"path":path,"id":photo_id,"photographer":item["photographer"],
                "alt":item["alt"],"url":item["url"],"width":image.width,"height":image.height}
        self.assets[path]=data
        self.credits[path]=credit
        return credit
