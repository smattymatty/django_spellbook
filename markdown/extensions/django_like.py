import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree


class DjangoLikeTagProcessor(BlockProcessor):
    RE_START = re.compile(r'{%\s*(\w+)([\s\S]+?)%}')
    RE_END = re.compile(r'{%\s*end(\w+)\s*%}')
    RE_CLASS = re.compile(r'\.([:\w-]+)')
    RE_ID = re.compile(r'#([\w-]+)')
    RE_ATTR = re.compile(r'([@:\w-]+)=[\'"]([^\'"]+)[\'"]')

    def test(self, parent, block):
        return self.RE_START.search(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE_START.search(block)

        if not m:
            return False

        tag = m.group(1)
        attrs_string = m.group(2)

        before = block[:m.start()]
        self.parser.parseBlocks(parent, [before])

        e = ElementTree.SubElement(parent, tag)
        self.parse_attributes(e, attrs_string)

        block = block[m.end():]
        while blocks and not self.RE_END.search(block):
            block += '\n' + blocks.pop(0)

        m = self.RE_END.search(block)
        if m:
            end_tag = m.group(1)
            if end_tag != tag:
                raise ValueError(f"Mismatched tags: {tag} and {end_tag}")
            block = block[:m.start()]

        self.parser.parseChunk(e, block)

        return True

    def parse_attributes(self, element, attrs_string):
        classes = []
        for class_match in self.RE_CLASS.finditer(attrs_string):
            classes.append(class_match.group(1))
        if classes:
            element.set('class', ' '.join(classes))

        id_match = self.RE_ID.search(attrs_string)
        if id_match:
            element.set('id', id_match.group(1))

        for attr_match in self.RE_ATTR.finditer(attrs_string):
            element.set(attr_match.group(1), attr_match.group(2))


class DjangoLikeTagExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            DjangoLikeTagProcessor(md.parser), 'django_like_tag', 175)


def makeExtension(**kwargs):
    return DjangoLikeTagExtension(**kwargs)
