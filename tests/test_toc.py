import unittest
from pathlib import Path
from django_spellbook.markdown.toc import TOCGenerator, TOCEntry


class TestTOCEntry(unittest.TestCase):
    def test_init_with_no_children(self):
        """Test TOCEntry initialization without children"""
        entry = TOCEntry(title="Test", url="/test")
        self.assertEqual(entry.title, "Test")
        self.assertEqual(entry.url, "/test")
        self.assertEqual(entry.children, {})

    def test_init_with_children(self):
        """Test TOCEntry initialization with children"""
        children = {"child": TOCEntry(title="Child", url="/child")}
        entry = TOCEntry(title="Parent", url="/parent", children=children)
        self.assertEqual(entry.title, "Parent")
        self.assertEqual(entry.url, "/parent")
        self.assertEqual(entry.children, children)


class TestTOCGenerator(unittest.TestCase):
    def setUp(self):
        self.toc = TOCGenerator()

    def test_root_initialization(self):
        """Test initial state of TOC generator"""
        self.assertEqual(self.toc.root.title, "root")
        self.assertEqual(self.toc.root.url, "")
        self.assertEqual(self.toc.root.children, {})

    def test_add_root_level_file(self):
        """Test adding a file at root level"""
        self.toc.add_entry(
            Path("index.md"),
            title="Home",
            url="/",
        )
        toc_dict = self.toc.get_toc()
        self.assertEqual(
            toc_dict["children"]["index"],
            {"title": "Home", "url": "/"}
        )

    def test_add_nested_file(self):
        """Test adding a file in nested directories"""
        self.toc.add_entry(
            Path("docs/guide/intro.md"),
            title="Introduction",
            url="/docs/guide/intro",
        )
        toc_dict = self.toc.get_toc()

        # Check the structure
        docs = toc_dict["children"]["docs"]
        self.assertEqual(docs["title"], "Docs")

        guide = docs["children"]["guide"]
        self.assertEqual(guide["title"], "Guide")

        intro = guide["children"]["intro"]
        self.assertEqual(intro["title"], "Introduction")
        self.assertEqual(intro["url"], "/docs/guide/intro")

    def test_multiple_files_same_directory(self):
        """Test adding multiple files to the same directory"""
        self.toc.add_entry(
            Path("docs/first.md"),
            title="First",
            url="/docs/first",
        )
        self.toc.add_entry(
            Path("docs/second.md"),
            title="Second",
            url="/docs/second",
        )

        toc_dict = self.toc.get_toc()
        docs_children = toc_dict["children"]["docs"]["children"]

        self.assertEqual(docs_children["first"]["title"], "First")
        self.assertEqual(docs_children["second"]["title"], "Second")

    def test_directory_title_formatting(self):
        """Test directory name formatting in TOC"""
        self.toc.add_entry(
            Path("getting-started/quick-start.md"),
            title="Quick Start",
            url="/getting-started/quick-start",
        )

        toc_dict = self.toc.get_toc()
        dir_entry = toc_dict["children"]["getting-started"]
        self.assertEqual(dir_entry["title"], "Getting Started")

    def test_mixed_structure(self):
        """Test mixed structure with files at different levels"""
        entries = [
            ("index.md", "Home", "/"),
            ("about.md", "About", "/about"),
            ("docs/index.md", "Documentation", "/docs"),
            ("docs/guide/start.md", "Getting Started", "/docs/guide/start"),
            ("docs/guide/advanced.md", "Advanced", "/docs/guide/advanced"),
        ]

        for path, title, url in entries:
            self.toc.add_entry(Path(path), title, url)

        toc_dict = self.toc.get_toc()
        root_children = toc_dict["children"]

        # Check root level
        self.assertEqual(root_children["index"]["title"], "Home")
        self.assertEqual(root_children["about"]["title"], "About")

        # Check nested structure
        docs = root_children["docs"]
        self.assertEqual(docs["children"]["index"]["title"], "Documentation")

        guide = docs["children"]["guide"]
        self.assertEqual(guide["children"]["start"]
                         ["title"], "Getting Started")
        self.assertEqual(guide["children"]["advanced"]["title"], "Advanced")

    def test_sorting(self):
        """Test that entries are sorted alphabetically"""
        entries = [
            ("z.md", "Z", "/z"),
            ("a.md", "A", "/a"),
            ("m.md", "M", "/m"),
        ]

        for path, title, url in entries:
            self.toc.add_entry(Path(path), title, url)

        toc_dict = self.toc.get_toc()
        children_keys = list(toc_dict["children"].keys())
        self.assertEqual(children_keys, sorted(children_keys))

    def test_empty_toc(self):
        """Test getting TOC with no entries"""
        toc_dict = self.toc.get_toc()
        self.assertEqual(
            toc_dict,
            {"title": "root", "url": ""}
        )

    def test_complex_paths(self):
        """Test handling of complex paths"""
        self.toc.add_entry(
            Path("a/very/deep/nested/structure/file.md"),
            title="Deep File",
            url="/a/very/deep/nested/structure/file",
        )

        current = self.toc.get_toc()
        for part in ["a", "very", "deep", "nested", "structure"]:
            self.assertIn(part, current["children"])
            current = current["children"][part]

        self.assertEqual(
            current["children"]["file"]["title"],
            "Deep File"
        )
