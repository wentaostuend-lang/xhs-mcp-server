import os
import re
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务
mcp = FastMCP("Xiaohongshu-Parser")

# 从环境变量中获取第三方 API 配置
API_ENDPOINT = os.getenv("XHS_API_ENDPOINT", "")
API_KEY = os.getenv("XHS_API_KEY", "")


@mcp.tool()
async def parse_xiaohongshu_link(url: str) -> str:
    """解析小红书帖子链接，提取标题、正文、作者及图片列表。
    
    Args:
        url: 小红书帖子的分享链接（支持带文字的短链或长链）
    """
    # 提取文案中包含的 HTTP/HTTPS 网址
    url_match = re.search(r'https?://[^\s]+', url)
    target_url = url_match.group(0) if url_match else url

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": target_url
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # 请求第三方 API
            response = await client.post(API_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 解析结构化字段
            note_data = data.get("data", data)
            title = note_data.get("title", "无标题")
            author = note_data.get("author", {}).get("nickname", "未知作者")
            content = note_data.get("desc") or note_data.get("content", "无正文")
            images = note_data.get("images", [])
            
            # 构建渲染给 AI 阅读的输出
            result = [
                f"📌 **标题**: {title}",
                f"👤 **作者**: {author}",
                f"📝 **正文内容**:\n{content}\n",
                f"🖼️ **图片列表 ({len(images)}张)**:"
            ]
            
            for idx, img in enumerate(images, 1):
                img_url = img if isinstance(img, str) else img.get("url", "")
                result.append(f"  {idx}. {img_url}")
                
            return "\n".join(result)

        except httpx.HTTPStatusError as e:
            return f"解析失败：第三方 API 返回状态码 {e.response.status_code}"
        except Exception as e:
            return f"解析异常：{str(e)}"

if __name__ == "__main__":
    mcp.run()
