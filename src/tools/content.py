"""Web content extraction tools."""

from fastmcp import Context, FastMCP

# Readability-like extraction via browser JS
# This extracts article content using heuristics similar to Mozilla Readability
# but implemented as inline JS that doesn't require bundling a library
ARTICLE_EXTRACT_JS = """
() => {
    // Try to find the main article content
    const selectors = [
        'article', '[role="main"]', 'main',
        '.post-content', '.article-content', '.entry-content',
        '.story-body', '#article-body', '.article-body'
    ];

    let articleEl = null;
    for (const sel of selectors) {
        articleEl = document.querySelector(sel);
        if (articleEl) break;
    }

    // Fall back to body if no article element found
    if (!articleEl) articleEl = document.body;

    // Extract clean text (remove scripts, styles, nav, footer, ads)
    const clone = articleEl.cloneNode(true);
    clone.querySelectorAll(
        'script, style, nav, footer, header, aside, .ad, .ads, '
        + '.advertisement, [role="navigation"], [role="banner"], '
        + '[role="contentinfo"]'
    ).forEach(el => el.remove());

    const text = clone.textContent
        .replace(/\\s+/g, ' ')
        .trim()
        .substring(0, 15000);

    // Extract title
    const title = document.querySelector('h1')?.textContent?.trim()
        || document.querySelector('title')?.textContent?.trim()
        || '';

    // Extract byline/author
    const byline = document.querySelector(
        '[rel="author"], .author, .byline, [itemprop="author"]'
    )?.textContent?.trim() || null;

    // Extract publish date
    const published =
        document.querySelector('time[datetime]')?.getAttribute('datetime')
        || document.querySelector(
            '[property="article:published_time"]'
        )?.getAttribute('content')
        || document.querySelector(
            'meta[name="date"]'
        )?.getAttribute('content')
        || null;

    // Extract excerpt/description
    const excerpt =
        document.querySelector(
            'meta[name="description"]'
        )?.getAttribute('content')
        || document.querySelector(
            'meta[property="og:description"]'
        )?.getAttribute('content')
        || text.substring(0, 300);

    return {
        title: title,
        byline: byline,
        published: published,
        excerpt: excerpt,
        content: text,
        length: text.length,
        source_url: window.location.href
    };
}
"""

METADATA_EXTRACT_JS = """
() => ({
    title: document.querySelector(
        'meta[property="og:title"]'
    )?.getAttribute('content')
        || document.querySelector('title')?.textContent?.trim(),
    description: document.querySelector(
        'meta[property="og:description"]'
    )?.getAttribute('content')
        || document.querySelector(
            'meta[name="description"]'
        )?.getAttribute('content'),
    image: document.querySelector(
        'meta[property="og:image"]'
    )?.getAttribute('content'),
    url: document.querySelector(
        'link[rel="canonical"]'
    )?.getAttribute('href')
        || window.location.href,
    site_name: document.querySelector(
        'meta[property="og:site_name"]'
    )?.getAttribute('content'),
    author: document.querySelector(
        'meta[name="author"]'
    )?.getAttribute('content')
        || document.querySelector('[rel="author"]')?.textContent?.trim(),
    published: document.querySelector(
        'meta[property="article:published_time"]'
    )?.getAttribute('content')
        || document.querySelector(
            'time[datetime]'
        )?.getAttribute('datetime'),
    type: document.querySelector(
        'meta[property="og:type"]'
    )?.getAttribute('content'),
    json_ld: (() => {
        try {
            const script = document.querySelector(
                'script[type="application/ld+json"]'
            );
            return script ? JSON.parse(script.textContent) : null;
        } catch { return null; }
    })(),
    favicon: document.querySelector(
        'link[rel="icon"]'
    )?.getAttribute('href')
        || document.querySelector(
            'link[rel="shortcut icon"]'
        )?.getAttribute('href')
})
"""


def register_content_tools(mcp: FastMCP) -> None:
    """Register web content extraction tools on the MCP server."""

    @mcp.tool
    async def web_extract_article(
        ctx: Context,
        include_metadata: bool = True,
    ) -> dict:
        """Extract clean article content from the current page.

        Uses browser-side JavaScript to parse the page DOM and extract
        the main article text, title, author, and publication date.
        Returns actual structured data, not an LLM instruction.

        Args:
            include_metadata: Whether to also extract page metadata
        """
        await ctx.report_progress(
            progress=0.3, total=1.0, message="Extracting article content"
        )

        try:
            article = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"expression": ARTICLE_EXTRACT_JS},
            )
        except Exception as e:
            article = {"error": str(e), "title": None, "content": None}

        result: dict = {"article": article}

        if include_metadata:
            await ctx.report_progress(
                progress=0.7, total=1.0, message="Extracting metadata"
            )
            try:
                metadata = await ctx.fastmcp.call_tool(
                    "playwright_browser_evaluate",
                    {"expression": METADATA_EXTRACT_JS},
                )
            except Exception as e:
                metadata = {"error": str(e)}
            result["metadata"] = metadata

        return result

    @mcp.tool
    async def web_extract_metadata(ctx: Context) -> dict:
        """Extract page metadata (OpenGraph, JSON-LD, meta tags).

        Returns structured metadata including title, description, image,
        author, publication date, and any JSON-LD structured data.
        """
        try:
            metadata = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"expression": METADATA_EXTRACT_JS},
            )
        except Exception as e:
            metadata = {"error": str(e)}

        return {"metadata": metadata, "url": "current page"}

    @mcp.tool
    async def web_save_pdf(
        ctx: Context,
        filename: str = "page.pdf",
    ) -> dict:
        """Save the current page as a PDF file.

        Note: PDF capability requires --caps=pdf on the Playwright subprocess, which is
        currently disabled to preserve the full proxied tool set. This tool may return
        an error until PDF capability is re-enabled in a future update.

        Args:
            filename: Output filename for the PDF
        """
        await ctx.report_progress(
            progress=0.5, total=1.0, message="Generating PDF"
        )

        pdf_tool_names = [
            "playwright_browser_pdf_save",
            "playwright_browser_save_as_pdf",
            "playwright_browser_save_pdf",
        ]

        for tool_name in pdf_tool_names:
            try:
                result = await ctx.fastmcp.call_tool(
                    tool_name, {"fileName": filename}
                )
                return {"saved": True, "filename": filename, "result": result}
            except Exception:
                continue

        return {
            "saved": False,
            "filename": filename,
            "error": (
                "PDF capability is not available. The Playwright subprocess "
                "needs --caps=pdf enabled, which currently restricts the full "
                "tool set. Alternatives: use playwright_browser_take_screenshot "
                "for visual capture, or use web_execute_js with window.print() "
                "for browser-native printing."
            ),
        }
