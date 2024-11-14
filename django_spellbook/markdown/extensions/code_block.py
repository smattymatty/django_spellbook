
'''import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree


class CodeBlockProcessor(BlockProcessor):
    RE_CODE_BLOCK = re.compile(r'```(\w+)?\s*([\s\S]+?)\s*```')

    def test(self, parent, block):
        # More flexible test that handles leading whitespace
        return '```' in block.strip()

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE_CODE_BLOCK.search(block)  # Use search instead of match

        if not m:
            return False

        language = m.group(1)
        content = m.group(2)

        # Create pre and code elements
        pre_elem = ElementTree.SubElement(parent, 'pre')
        code_elem = ElementTree.SubElement(pre_elem, 'code')

        if language:
            code_elem.set('data-language', language)
            code_elem.set('class', f'language-{language}')

        # Preserve whitespace but trim extra newlines
        code_elem.text = content.strip()

        # Handle remaining content
        remaining = block[m.end():].lstrip()
        if remaining:
            blocks.insert(0, remaining)

        return True


class CodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            CodeBlockProcessor(md.parser), 'code_block', 180)


def makeExtension(**kwargs):
    return CodeBlockExtension(**kwargs)
'''
