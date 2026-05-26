#!/usr/bin/env python3
"""
GitHub Actions 定时任务脚本
每天北京时间 9:00 和 23:00 执行
"""

import httpx
import re
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

GITHUB_URL = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/README_zh.md"
REPO_RAW_BASE = "https://raw.githubusercontent.com/YouMind-OpenLab/awesome-gpt-image-2/main/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "frontend" / "public" / "data"
ARTICLE_FILE = DATA_DIR / "article.json"

def clean_text(text: str) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    value = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", value)
    return value


def parse_markdown(markdown_content: str) -> dict:
    title_match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
    title = clean_text(title_match.group(1)) if title_match else "GPT Image 2 图文精选"

    heading_pattern = re.compile(r"^(##+)\s+(.+)$")
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

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        heading_match = heading_pattern.match(line)
        if heading_match:
            current_heading = clean_text(heading_match.group(2))
            current_section = current_heading
            if current_heading.startswith("No."):
                current_title = current_heading
                current_description = ""
                last_prompt = ""
            context_buffer = []
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
            continue

        if line.startswith("####") and "提示词" in line:
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
                }
            )
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
                }
            )
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

def sync_article():
    """同步 GitHub 文章"""
    print(f"[{datetime.now(timezone.utc).isoformat()}] 开始同步文章...")
    
    try:
        # 获取 GitHub 内容
        print("正在从 GitHub 获取内容...")
        with httpx.Client(timeout=30.0) as client:
            response = client.get(GITHUB_URL)
            response.raise_for_status()
            
        markdown_content = response.text
        parsed = parse_markdown(markdown_content)
        update_time = datetime.now(timezone.utc).isoformat()
        
        article = {
            "title": parsed["title"],
            "intro": parsed["intro"],
            "blocks": parsed["blocks"],
            "updateAt": update_time,
            "source": GITHUB_URL
        }
        
        # 保存数据
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
        return False

if __name__ == "__main__":
    success = sync_article()
    sys.exit(0 if success else 1)
