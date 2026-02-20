"""Skills directory provider configuration."""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider


def mount_skills(mcp: FastMCP) -> None:
    """Register the skills directory provider.

    Scans the skills/ directory for folders containing SKILL.md files
    and exposes them as MCP resources.
    """
    skills_dir = Path(__file__).parent.parent.parent / "skills"

    if skills_dir.exists():
        mcp.add_provider(SkillsDirectoryProvider(roots=[skills_dir]))
