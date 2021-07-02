import re
import textwrap
from typing import Optional, Iterable, Iterator


class MarkdownDocument:
    def __init__(self):
        self.indent = '    '
        self.sections = []

    def add_section(self, text: str):
        self.sections.append(text)

    def add(self, doc: 'MarkdownDocument'):
        self.sections.extend(doc.sections)

    def add_all(self, docs: 'Iterable[MarkdownDocument]'):
        for doc in docs:
            self.add(doc)

    def text(self, text: str):
        if text:
            self.add_section(self.replace_newlines(text))

    def heading(self, level: int, body: str):
        self.add_section(textwrap.indent(body, '#' * level + ' '))

    def admonition(self, style: str, title: str, body: str, *, collapsible: bool = False):
        title = f' "{title}"' if title is not None else ''
        prefix = "???" if collapsible else "!!!"
        self.add_section(f'{prefix} {style}{title}\n{textwrap.indent(self.replace_newlines(body), self.indent)}')

    @staticmethod
    def escape_markdown(text):
        return re.sub(r'([|\\*])', r'\\\1', text)

    @staticmethod
    def replace_newlines(text: str):
        return text.replace('\n', '  \n')

    def get(self):
        return '\n\n'.join(self.sections)

    def __str__(self):
        return self.get()
