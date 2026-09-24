import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcp.server.mcpserver.resources import DirectoryResource


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A directory with top-level files, a nested file, and a subdirectory."""
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("c", encoding="utf-8")
    return tmp_path


async def _listing(resource: DirectoryResource) -> list[str]:
    return json.loads(await resource.read())["files"]


@pytest.mark.anyio
async def test_read_lists_top_level_files_sorted_without_directories(tree: Path):
    resource = DirectoryResource(uri="dir://tree", name="tree", path=tree)
    assert await _listing(resource) == ["a.md", "b.txt"]


@pytest.mark.anyio
async def test_recursive_read_uses_forward_slashes_on_every_platform(tree: Path):
    """Nested paths use `/` so the JSON listing is identical on Windows and POSIX."""
    resource = DirectoryResource(uri="dir://tree", name="tree", path=tree, recursive=True)
    assert await _listing(resource) == ["a.md", "b.txt", "sub/c.txt"]


@pytest.mark.anyio
async def test_pattern_filters_listing(tree: Path):
    resource = DirectoryResource(uri="dir://tree", name="tree", path=tree, pattern="*.txt")
    assert await _listing(resource) == ["b.txt"]


@pytest.mark.anyio
async def test_recursive_pattern_filters_nested_listing(tree: Path):
    resource = DirectoryResource(uri="dir://tree", name="tree", path=tree, pattern="*.txt", recursive=True)
    assert await _listing(resource) == ["b.txt", "sub/c.txt"]


@pytest.mark.anyio
async def test_read_missing_directory_raises_file_not_found(tmp_path: Path):
    resource = DirectoryResource(uri="dir://missing", name="missing", path=tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        await resource.read()


@pytest.mark.anyio
async def test_read_file_path_raises_not_a_directory(tree: Path):
    resource = DirectoryResource(uri="dir://file", name="file", path=tree / "a.md")
    with pytest.raises(NotADirectoryError):
        await resource.read()


def test_relative_path_is_rejected():
    with pytest.raises(ValidationError):
        DirectoryResource(uri="dir://rel", name="rel", path=Path("relative/dir"))
