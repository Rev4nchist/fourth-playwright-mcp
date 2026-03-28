"""Web performance and accessibility tools."""

from fastmcp import Context, FastMCP

PERFORMANCE_JS = """
() => {
    const perf = {};

    // Navigation Timing
    const nav = performance.getEntriesByType('navigation')[0];
    if (nav) {
        perf.navigation = {
            dns_ms: Math.round(nav.domainLookupEnd - nav.domainLookupStart),
            tcp_ms: Math.round(nav.connectEnd - nav.connectStart),
            ttfb_ms: Math.round(nav.responseStart - nav.requestStart),
            download_ms: Math.round(nav.responseEnd - nav.responseStart),
            dom_interactive_ms: Math.round(nav.domInteractive - nav.startTime),
            dom_complete_ms: Math.round(nav.domComplete - nav.startTime),
            load_event_ms: Math.round(nav.loadEventEnd - nav.startTime),
            transfer_size_kb: Math.round(nav.transferSize / 1024),
        };
    }

    // Resource summary
    const resources = performance.getEntriesByType('resource');
    perf.resources = {
        count: resources.length,
        total_size_kb: Math.round(
            resources.reduce((s, r) => s + (r.transferSize || 0), 0) / 1024
        ),
        by_type: {},
    };
    resources.forEach(r => {
        const type = r.initiatorType || 'other';
        if (!perf.resources.by_type[type]) {
            perf.resources.by_type[type] = { count: 0, size_kb: 0, slowest_ms: 0 };
        }
        perf.resources.by_type[type].count++;
        perf.resources.by_type[type].size_kb += Math.round(
            (r.transferSize || 0) / 1024
        );
        perf.resources.by_type[type].slowest_ms = Math.max(
            perf.resources.by_type[type].slowest_ms, Math.round(r.duration)
        );
    });

    // Largest Contentful Paint
    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
    if (lcpEntries.length > 0) {
        const lcp = lcpEntries[lcpEntries.length - 1];
        perf.lcp_ms = Math.round(lcp.startTime);
        perf.lcp_element = lcp.element
            ? lcp.element.tagName + (lcp.element.id ? '#' + lcp.element.id : '')
            : null;
    }

    // Cumulative Layout Shift
    let cls = 0;
    performance.getEntriesByType('layout-shift').forEach(entry => {
        if (!entry.hadRecentInput) cls += entry.value;
    });
    perf.cls = Math.round(cls * 1000) / 1000;

    // First Contentful Paint
    const fcpEntries = performance.getEntriesByType('paint');
    fcpEntries.forEach(entry => {
        if (entry.name === 'first-contentful-paint') {
            perf.fcp_ms = Math.round(entry.startTime);
        }
        if (entry.name === 'first-paint') {
            perf.fp_ms = Math.round(entry.startTime);
        }
    });

    // Page info
    perf.url = window.location.href;
    perf.title = document.title;

    return perf;
}
"""

ACCESSIBILITY_JS = """
() => {
    const issues = [];

    // Images without alt text
    document.querySelectorAll('img').forEach(img => {
        if (!img.alt && !img.getAttribute('role')?.includes('presentation')) {
            issues.push({
                type: 'img-no-alt',
                severity: 'critical',
                element: img.tagName,
                selector: img.id ? '#' + img.id : img.src?.substring(0, 80),
                message: 'Image missing alt text'
            });
        }
    });

    // Form inputs without labels
    document.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.type === 'hidden') return;
        const hasLabel = el.labels?.length > 0
            || el.getAttribute('aria-label')
            || el.getAttribute('aria-labelledby')
            || el.getAttribute('title')
            || el.getAttribute('placeholder');
        if (!hasLabel) {
            issues.push({
                type: 'input-no-label',
                severity: 'critical',
                element: el.tagName + '[type=' + (el.type || 'text') + ']',
                selector: el.id ? '#' + el.id : el.name || '(anonymous)',
                message: 'Form input has no accessible label'
            });
        }
    });

    // Heading hierarchy skip (e.g., h1 -> h3 with no h2)
    const headings = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')];
    let prevLevel = 0;
    headings.forEach(h => {
        const level = parseInt(h.tagName[1]);
        if (prevLevel > 0 && level > prevLevel + 1) {
            issues.push({
                type: 'heading-skip',
                severity: 'warning',
                element: h.tagName,
                selector: h.textContent.trim().substring(0, 50),
                message: 'Heading level skipped: h' + prevLevel + ' -> h' + level
            });
        }
        prevLevel = level;
    });

    // Buttons/links with no accessible name
    document.querySelectorAll('button, a[href], [role="button"]').forEach(el => {
        const name = el.textContent.trim()
            || el.getAttribute('aria-label')
            || el.getAttribute('title')
            || el.querySelector('img')?.alt;
        if (!name) {
            issues.push({
                type: 'no-accessible-name',
                severity: 'critical',
                element: el.tagName,
                selector: el.id
                    ? '#' + el.id
                    : el.className?.split(' ')[0] || '(anonymous)',
                message: 'Interactive element has no accessible name'
            });
        }
    });

    // Missing lang attribute
    if (!document.documentElement.lang) {
        issues.push({
            type: 'missing-lang',
            severity: 'warning',
            element: 'html',
            selector: 'html',
            message: 'Document is missing lang attribute'
        });
    }

    // ARIA role validation (basic)
    const validRoles = [
        'alert', 'alertdialog', 'application', 'article', 'banner',
        'button', 'cell', 'checkbox', 'columnheader', 'combobox',
        'complementary', 'contentinfo', 'definition', 'dialog',
        'directory', 'document', 'feed', 'figure', 'form', 'grid',
        'gridcell', 'group', 'heading', 'img', 'link', 'list',
        'listbox', 'listitem', 'log', 'main', 'marquee', 'math',
        'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
        'menuitemradio', 'navigation', 'none', 'note', 'option',
        'presentation', 'progressbar', 'radio', 'radiogroup', 'region',
        'row', 'rowgroup', 'rowheader', 'scrollbar', 'search',
        'searchbox', 'separator', 'slider', 'spinbutton', 'status',
        'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term',
        'textbox', 'timer', 'toolbar', 'tooltip', 'tree', 'treegrid',
        'treeitem'
    ];
    document.querySelectorAll('[role]').forEach(el => {
        const role = el.getAttribute('role');
        if (!validRoles.includes(role)) {
            issues.push({
                type: 'invalid-aria-role',
                severity: 'warning',
                element: el.tagName,
                selector: el.id ? '#' + el.id : '(anonymous)',
                message: 'Invalid ARIA role: "' + role + '"'
            });
        }
    });

    // Summary
    const summary = {
        total_issues: issues.length,
        critical: issues.filter(i => i.severity === 'critical').length,
        warnings: issues.filter(i => i.severity === 'warning').length,
        by_type: {}
    };
    issues.forEach(i => {
        summary.by_type[i.type] = (summary.by_type[i.type] || 0) + 1;
    });

    return { issues, summary, url: window.location.href, title: document.title };
}
"""


def register_performance_tools(mcp: FastMCP) -> None:
    """Register web performance and accessibility tools on the MCP server."""

    @mcp.tool
    async def web_performance(
        ctx: Context,
        include_resource_details: bool = False,
    ) -> dict:
        """Profile the current page's performance metrics.

        Returns Navigation Timing (TTFB, DOM interactive, load event),
        Core Web Vitals (LCP, CLS, FCP), and resource loading summary.
        All metrics are extracted via the browser's Performance API.

        Args:
            include_resource_details: Include per-resource timing breakdown
                                     (top 50 resources by load time)
        """
        try:
            metrics = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"function": PERFORMANCE_JS},
            )
            if not include_resource_details and isinstance(metrics, dict):
                metrics.pop("resources_detail", None)
            return {"success": True, "metrics": metrics}
        except Exception as e:
            return {"success": False, "metrics": None, "error": str(e)}

    @mcp.tool
    async def web_accessibility_audit(
        ctx: Context,
        severity_filter: str = "all",
    ) -> dict:
        """Run an accessibility audit on the current page.

        Checks for common accessibility issues: images without alt text,
        form inputs without labels, heading hierarchy skips, interactive
        elements without accessible names, missing lang attribute, and
        invalid ARIA roles.

        Returns structured issues with severity levels and a summary.

        Args:
            severity_filter: Filter issues by severity level.
                           "all" (default), "critical", or "warning".
        """
        try:
            audit = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"function": ACCESSIBILITY_JS},
            )
            if severity_filter != "all" and isinstance(audit, dict):
                if "issues" in audit:
                    audit["issues"] = [
                        i for i in audit["issues"]
                        if i.get("severity") == severity_filter
                    ]
                    audit["summary"] = {
                        "total_issues": len(audit["issues"]),
                        "critical": sum(
                            1 for i in audit["issues"]
                            if i.get("severity") == "critical"
                        ),
                        "warnings": sum(
                            1 for i in audit["issues"]
                            if i.get("severity") == "warning"
                        ),
                        "by_type": {},
                    }
                    for i in audit["issues"]:
                        t = i.get("type", "unknown")
                        audit["summary"]["by_type"][t] = (
                            audit["summary"]["by_type"].get(t, 0) + 1
                        )
            return {"success": True, "audit": audit}
        except Exception as e:
            return {"success": False, "audit": None, "error": str(e)}
