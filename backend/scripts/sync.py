#!/usr/bin/env python3
"""
GitHub Actions 定时任务脚本
每天北京时间 9:00 和 23:00 执行
"""

import httpx
import re
import json
import binascii
from datetime import datetime, timezone
from pathlib import Path
import sys

GITHUB_URL = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/README_zh.md"
REPO_RAW_BASE = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/"
COMMITS_API_URL = "https://api.github.com/repos/YouMind-OpenLab/awesome-gpt-image-2/commits"
COMMITS_PAGE_URL = "https://github.com/YouMind-OpenLab/awesome-gpt-image-2/commits/main/README_zh.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "frontend" / "public" / "data"
ARTICLE_FILE = DATA_DIR / "article.json"
CAMO_CACHE_FILE = DATA_DIR / "camo_cache.json"

CMS_ASSETS_PREFIX = "cms-assets.youmind.com"


def fetch_recent_history(client: httpx.Client) -> list:
    try:
        response = client.get(
            COMMITS_API_URL,
            params={"path": "README_zh.md", "sha": "main", "per_page": 10},
        )
        response.raise_for_status()
        commits = response.json()
        history = []
        for commit in commits:
            sha = commit.get("sha", "")
            commit_info = commit.get("commit", {})
            author_info = commit_info.get("author", {})
            history.append(
                {
                    "sha": sha[:7],
                    "message": clean_text((commit_info.get("message") or "").splitlines()[0]),
                    "date": author_info.get("date", ""),
                    "url": commit.get("html_url", ""),
                }
            )
        return history
    except Exception:
        return []


def fetch_markdown_by_sha(client: httpx.Client, sha: str) -> str:
    url = f"https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/{sha}/README_zh.md"
    response = client.get(url)
    response.raise_for_status()
    return response.text

def clean_text(text: str) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    value = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", value)
    return value


def parse_markdown(markdown_content: str) -> dict:
    title_match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
    title = clean_text(title_match.group(1)) if title_match else "GPT Image 2 图文精选"

    no_heading_pattern = re.compile(r"^###\s+(No\.\s*\d+:\s+.+)$")
    image_heading_pattern = re.compile(r"^#####\s+(Image\s+\d+)\s*$", re.IGNORECASE)
    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
    html_image_pattern = re.compile(r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>', re.IGNORECASE)

    lines = markdown_content.splitlines()
    current_section = "精选图集"
    blocks = []
    context_buffer = []
    last_prompt = ""
    current_title = ""
    current_description = ""
    in_prompt_block = False
    prompt_lines = []
    current_x_url = ""
    current_block_indexes = []
    current_published_at = ""
    current_author = ""
    current_language = ""
    expect_description_text = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        no_heading_match = no_heading_pattern.match(line)
        if no_heading_match:
            current_title = clean_text(no_heading_match.group(1))
            current_section = current_title
            current_description = ""
            last_prompt = ""
            current_x_url = ""
            current_block_indexes = []
            current_published_at = ""
            current_author = ""
            current_language = ""
            expect_description_text = False
            context_buffer = []
            continue

        image_heading_match = image_heading_pattern.match(line)
        if image_heading_match:
            current_section = clean_text(image_heading_match.group(1))
            continue

        if line.startswith("- **来源:**"):
            source_match = re.search(r"\((https?://[^)\s]+)\)", line)
            if source_match:
                current_x_url = source_match.group(1)
                for idx in current_block_indexes:
                    if 0 <= idx < len(blocks):
                        blocks[idx]["xUrl"] = current_x_url
            continue

        if line.startswith("- **发布时间:**"):
            published_match = re.search(r"- \*\*发布时间:\*\*\s*(.+)$", line)
            if published_match:
                current_published_at = clean_text(published_match.group(1))
                for idx in current_block_indexes:
                    if 0 <= idx < len(blocks):
                        blocks[idx]["publishedAt"] = current_published_at
            continue

        if line.startswith("- **作者:**"):
            author_match = re.search(r"- \*\*作者:\*\*\s*(.+)$", line)
            if author_match:
                current_author = clean_text(author_match.group(1))
                for idx in current_block_indexes:
                    if 0 <= idx < len(blocks):
                        blocks[idx]["author"] = current_author
            continue

        if line.startswith("- **多语言:**"):
            lang_match = re.search(r"- \*\*多语言:\*\*\s*(.+)$", line)
            if lang_match:
                current_language = clean_text(lang_match.group(1))
                for idx in current_block_indexes:
                    if 0 <= idx < len(blocks):
                        blocks[idx]["language"] = current_language
            continue

        if line.startswith("```"):
            if in_prompt_block:
                in_prompt_block = False
                if prompt_lines:
                    last_prompt = "\n".join(prompt_lines).strip()
                    prompt_lines = []
            else:
                in_prompt_block = True
                prompt_lines = []
            continue

        if in_prompt_block:
            prompt_lines.append(raw_line.rstrip())
            continue

        if line.startswith("####") and "描述" in line:
            current_description = ""
            expect_description_text = True
            continue

        if line.startswith("####") and "提示词" in line:
            expect_description_text = False
            continue

        if line.startswith("####"):
            expect_description_text = False

        if expect_description_text and line and not line.startswith("#") and not line.startswith("!") and not line.startswith("<"):
            current_description = clean_text(re.sub(r"^[\-*>\s]*", "", line))
            expect_description_text = False
            continue

        if current_description == "" and line and not line.startswith("#") and not line.startswith("!") and not line.startswith("<") and "提示词" not in line:
            if context_buffer and context_buffer[-1].startswith("No."):
                pass
            elif current_title:
                current_description = clean_text(re.sub(r"^[\-*>\s]*", "", line))

        if "提示词" in line or "prompt" in line.lower():
            last_prompt = clean_text(re.sub(r"^[\-*>\s]*", "", line))
            context_buffer.append(last_prompt)
            context_buffer = context_buffer[-4:]
            continue

        image_match = image_pattern.search(line)
        if image_match:
            caption = clean_text(image_match.group(1))
            image_url = normalize_image_url(image_match.group(2))
            if not image_url or is_noise_image(image_url):
                continue

            description = current_description or (context_buffer[-1] if context_buffer else "")
            if not description:
                description = caption or current_section

            block_title = current_title or caption or current_section
            blocks.append(
                {
                    "section": current_section,
                    "title": block_title,
                    "description": description,
                    "prompt": last_prompt,
                    "image": image_url,
                    "xUrl": current_x_url,
                    "publishedAt": current_published_at,
                    "author": current_author,
                    "language": current_language,
                }
            )
            current_block_indexes.append(len(blocks) - 1)
            continue

        html_img_match = html_image_pattern.search(line)
        if html_img_match:
            image_url = normalize_image_url(html_img_match.group(1))
            caption = clean_text(html_img_match.group(2))
            if not image_url or is_noise_image(image_url):
                continue

            description = current_description or caption or current_section
            block_title = current_title or caption or current_section
            blocks.append(
                {
                    "section": current_section,
                    "title": block_title,
                    "description": description,
                    "prompt": last_prompt,
                    "image": image_url,
                    "xUrl": current_x_url,
                    "publishedAt": current_published_at,
                    "author": current_author,
                    "language": current_language,
                }
            )
            current_block_indexes.append(len(blocks) - 1)
            continue

        if line.startswith("#"):
            continue

        plain = clean_text(re.sub(r"^[\-*>\s]*", "", line))
        if plain:
            context_buffer.append(plain)
            context_buffer = context_buffer[-4:]

    intro = "围绕图片、描述与提示词重组的每日精选内容，适合直接发布为图文文章。"
    return {
        "title": title,
        "intro": intro,
        "blocks": blocks,
    }


def normalize_image_url(url: str) -> str:
    value = url.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"{REPO_RAW_BASE}{value.lstrip('./')}"


def is_noise_image(url: str) -> bool:
    noise_keywords = [
        "shields.io",
        "awesome.re/badge",
        "actions/workflows",
        "marketing-assets.youmind.com",
        "badge.svg",
        "cover-zh",
        "star-history.com",
    ]
    return any(keyword in url for keyword in noise_keywords)

def load_camo_cache() -> dict:
    if CAMO_CACHE_FILE.exists():
        try:
            return json.loads(CAMO_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_camo_cache(cache: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CAMO_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def build_camo_url_map(client: httpx.Client, markdown_content: str) -> dict:
    cms_urls = set()
    for match in re.finditer(r"!\[([^\]]*)\]\((https?://cms-assets\.youmind\.com/[^)\s]+)\)", markdown_content):
        cms_urls.add(match.group(2))
    if not cms_urls:
        return {}

    md_snippets = []
    for u in list(cms_urls)[:50]:
        md_snippets.append(f"![]({u})")

    try:
        resp = client.post(
            "https://api.github.com/markdown",
            json={"text": "\n\n".join(md_snippets), "mode": "gfm"},
            timeout=30.0,
        )
        resp.raise_for_status()
        html = resp.text

        camo_map = {}
        for u in cms_urls:
            h = binascii.crc32(u.encode()) & 0xFFFFFFFF
            camo_base = f"https://camo.githubusercontent.com/{h:x}/"
            pattern = re.escape(f"https://camo.githubusercontent.com/{h:x}/") + r"[a-f0-9]{40}"
            found = re.findall(pattern, html)
            if found:
                camo_map[u] = found[0]
        return camo_map
    except Exception as e:
        print(f"  build_camo_url_map failed: {e}")
        return {}


def build_camo_map_for_urls(client: httpx.Client, urls: list[str]) -> dict:
    if not urls:
        return {}
    md_snippets = [f"![]({u})" for u in urls]
    try:
        resp = client.post(
            "https://api.github.com/markdown",
            json={"text": "\n\n".join(md_snippets), "mode": "gfm"},
            timeout=30.0,
        )
        resp.raise_for_status()
        html = resp.text
        camo_map = {}
        for u in urls:
            h = binascii.crc32(u.encode()) & 0xFFFFFFFF
            camo_base = f"https://camo.githubusercontent.com/{h:x}/"
            pattern = re.escape(camo_base) + r"[a-f0-9]{40}"
            found = re.findall(pattern, html)
            if found:
                camo_map[u] = found[0]
        return camo_map
    except Exception as e:
        print(f"  build_camo_map_for_urls failed: {e}")
        return {}


def collect_cms_urls(blocks: list[dict]) -> set[str]:
    urls = set()
    for b in blocks:
        img = b.get("image", "")
        if CMS_ASSETS_PREFIX in img:
            urls.add(img)
    return urls


def apply_camo_map(blocks: list[dict], camo_map: dict) -> int:
    replaced = 0
    for b in blocks:
        img = b.get("image", "")
        if img in camo_map:
            b["image"] = camo_map[img]
            replaced += 1
    return replaced
def sync_article():
    """同步 GitHub 文章"""
    print(f"[{datetime.now(timezone.utc).isoformat()}] 开始同步文章...")

    camo_cache = load_camo_cache()
    print(f"  已加载 camo_cache: {len(camo_cache)} 条")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(GITHUB_URL)
            response.raise_for_status()
            history = fetch_recent_history(client)
            markdown_content = response.text
            parsed = parse_markdown(markdown_content)

            all_cms_urls = collect_cms_urls(parsed["blocks"])

            history_versions = []
            for item in history:
                sha = item.get("sha", "")
                if not sha:
                    continue
                try:
                    version_markdown = fetch_markdown_by_sha(client, sha)
                    parsed_version = parse_markdown(version_markdown)
                    all_cms_urls.update(collect_cms_urls(parsed_version["blocks"]))
                    history_versions.append(
                        {
                            "sha": sha,
                            "message": item.get("message", ""),
                            "date": item.get("date", ""),
                            "title": parsed_version["title"],
                            "intro": parsed_version["intro"],
                            "blocks": parsed_version["blocks"],
                        }
                    )
                except Exception:
                    continue

            unresolved = [u for u in all_cms_urls if u not in camo_cache]
            if unresolved:
                print(f"  未解析的 cms-assets URL: {len(unresolved)}，从主 README 构建 camo 映射...")
                new_map = build_camo_url_map(client, markdown_content)
                camo_cache.update(new_map)
                unresolved = [u for u in unresolved if u not in camo_cache]
            if unresolved:
                print(f"  仍有 {len(unresolved)} 个未解析，批量构建...")
                new_map = build_camo_map_for_urls(client, unresolved)
                camo_cache.update(new_map)
                save_camo_cache(camo_cache)

            replaced_count = apply_camo_map(parsed["blocks"], camo_cache)
            print(f"  当前版本替换: {replaced_count} 张")

            for hv in history_versions:
                r = apply_camo_map(hv["blocks"], camo_cache)
                if r:
                    print(f"  历史版本 {hv['sha']} 替换: {r} 张")

            remaining = collect_cms_urls(parsed["blocks"])
            for hv in history_versions:
                remaining.update(collect_cms_urls(hv["blocks"]))
            remaining = [u for u in remaining if u not in camo_cache]
            if remaining:
                print(f"  警告: 仍有 {len(remaining)} 个未替换的 cms-assets URL")
                for u in remaining[:5]:
                    print(f"    {u}")

            save_camo_cache(camo_cache)

        update_time = datetime.now(timezone.utc).isoformat()

        article = {
            "title": parsed["title"],
            "intro": parsed["intro"],
            "blocks": parsed["blocks"],
            "updateAt": update_time,
            "source": GITHUB_URL,
            "historyPage": COMMITS_PAGE_URL,
            "recentHistory": history,
            "historyVersions": history_versions,
        }

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(ARTICLE_FILE, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        print(f"Sync success: {parsed['title']}")
        print(f"  更新时间：{update_time}")
        print(f"  保存位置：{ARTICLE_FILE}")

        return True

    except httpx.HTTPError as e:
        print(f"✗ GitHub API 请求失败：{e}")
        return False
    except Exception as e:
        print(f"✗ 同步失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ 同步失败：{e}")
        return False

if __name__ == "__main__":
    success = sync_article()
    sys.exit(0 if success else 1)
