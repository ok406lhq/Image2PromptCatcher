from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import re
import json
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="GPT-Image2 Article API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Article(BaseModel):
    title: str
    intro: str
    blocks: list[dict]
    updateAt: str
    source: str

class SyncRequest(BaseModel):
    force: bool = False

GITHUB_URL = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/README_zh.md"
REPO_RAW_BASE = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/"
COMMITS_API_URL = "https://api.github.com/repos/YouMind-OpenLab/awesome-gpt-image-2/commits"
COMMITS_PAGE_URL = "https://github.com/YouMind-OpenLab/awesome-gpt-image-2/commits/main/README_zh.md"
DATA_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data"


def fetch_markdown_by_sha(sha: str) -> str:
    url = f"https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/{sha}/README_zh.md"
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
    return response.text


def fetch_recent_history() -> list:
    try:
        with httpx.Client(timeout=30.0) as client:
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
    blocks: list[dict] = []
    context_buffer: list[str] = []
    last_prompt = ""
    current_title = ""
    current_description = ""
    in_prompt_block = False
    prompt_lines: list[str] = []
    current_x_url = ""
    current_block_indexes: list[int] = []
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
            image_url = image_match.group(2)
            image_url = normalize_image_url(image_url)
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

@app.get("/")
def root():
    return {"message": "GPT-Image2 Article API", "version": "1.0.0"}

@app.get("/api/article", response_model=Article)
def get_article():
    """获取当前 cached 的文章数据"""
    article_file = DATA_DIR / "article.json"
    
    if not article_file.exists():
        raise HTTPException(status_code=404, detail="没有可用的文章数据，请先运行同步任务")
    
    with open(article_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

@app.post("/api/sync", response_model=Article)
async def sync_article(request: SyncRequest = SyncRequest()):
    """从 GitHub 同步最新文章"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GITHUB_URL)
            response.raise_for_status()
            
        markdown_content = response.text
        parsed = parse_markdown(markdown_content)
        history = fetch_recent_history()
        history_versions = []
        for item in history:
            sha = item.get("sha", "")
            if not sha:
                continue
            try:
                version_markdown = fetch_markdown_by_sha(sha)
                parsed_version = parse_markdown(version_markdown)
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
        
        # 保存到 frontend/public/data/article.json
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "article.json", 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        
        return article
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"GitHub API 请求失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文章失败：{str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
