#!/usr/bin/env python3

from mistune import create_markdown
from mistune.renderers import BaseRenderer
import re


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


def order_key(a, b):
    idx_dict = {}
    idx_dict["all"] = 0
    idx_dict["Spring"] = 1
    idx_dict["Summer"] = 2
    idx_dict["Fall"] = 3
    author_a, year_a, semester_a = a
    author_b, year_b, semester_b = b
    author_a = author_a.lower()
    author_b = author_b.lower()
    semester_idx_a = idx_dict[semester_a]
    semester_idx_b = idx_dict[semester_b]
    if year_a < year_b:
        return True, None
    if year_a > year_b:
        return False, "Year"
    if year_a == year_b:
        if semester_idx_a < semester_idx_b:
            return True, None
        if semester_idx_a > semester_idx_b:
            return False, "Semester should be Spring < Summer < Fall"
        if semester_idx_a == semester_idx_b:
            if author_a <= author_b:
                return True, None
            else:
                return False, "Author should be Aaa < bBb < Ccc"


def parse_info(line):
    x = re.search(r"\[@(.*?), (.*?) (.*?)\]", line)
    if not x:
        x = re.search(r"\[#(.*?)\]", line)
        if x:
            return True, None
        else:
            return False, f"failed to parse: no [@user, year semester] found"
    author, year, semester = x.group(1), x.group(2), x.group(3)
    if semester not in ["Spring", "Fall", "all", "Summer"]:
        return False, f"unsupported semester: {semester}"
    return True, (author, year, semester)


def in_sequence(a, b):
    seq = []
    chunk = [a, b]
    for line in chunk:
        success, result = parse_info(line)
        if not success or not result:
            if line == a:
                return False, "previous line is broken"
            else:
                return False, "failed to parse: unknown"
        author, year, semester = result
        seq.append((author, year, semester))
    for i in range(len(seq) - 1):
        success, reason = order_key(seq[i], seq[i + 1])
        if not success:
            return False, f"list not sorted: {reason}"
    return True, None


def fail(text):
    return ' ❌ \033[31;1m' + text + '\033[0m'


def ok(text):
    return '  ✅ \033[32;1m' + text + '\033[0m'

# https://gist.github.com/waylan/ba297e1c46dc5a16cac6347387bc1452


ESCAPE_CHAR = re.compile(r'(?<!\\)([\\`*_()\[\]#+-])')
UL_BULLET = re.compile(r'(?<=^)(\*)( +)', re.MULTILINE)

parse_success = True


def indent(text, level, tab_length=4):
    ''' Indent block of text by level '''
    return '\n'.join(f'{" "*tab_length*level}{line}' for line in text.split('\n'))


class MdRenderer(BaseRenderer):
    NAME = 'md'
    IS_TREE = False

    def __init__(self):
        self.lst_list_level = 0
        self.lst_list_item = ""
        self.check_begin = False

    def text(self, text):
        # TODO: escaping is probably more agressive than it needs to be.
        return text

    def link(self, link, text=None, title=None):
        if link == text or ('@' in text and link.startswith('mailto:') and link[7:] == text):
            # Autolink
            return f'<{text}>'
        text = link if text is None else text
        title = f' "{title}"' if title is not None else ''
        return f'[{text}]({link}{title})'

    def image(self, src, alt="", title=None):
        title = f' "{title}"' if title is not None else ''
        return f'![{alt}]({src}{title})'

    def emphasis(self, text):
        return f'*{text}*'

    def strong(self, text):
        return f'**{text}**'

    def codespan(self, text):
        # TODO: account for double backticks in code span.
        if '`' in text:
            return f'`` {text} ``'
        return f'`{text}`'

    def linebreak(self):
        return '  \n'

    def inline_html(self, html):
        return html

    def paragraph(self, text):
        return f'{text}\n\n'

    def heading(self, text, level):
        append_text = ""
        if level == 3:
            result = re.match("(.*) - (.*)", text)
            if result:
                self.check_begin = True

        return f'{"#"*level} {text}{append_text}\n\n'

    def newline(self):
        return '\n'

    def thematic_break(self):
        return '- - -\n\n'

    def block_text(self, text):
        return text

    def block_code(self, code, info=None):
        info = info or ''
        code = code.rstrip('\n')
        return f'```{info}\n{code}\n```\n\n'

    def block_quote(self, text):
        return '\n'.join([f'> {line}' for line in text.strip().splitlines()]) + '\n'

    def block_html(self, html):
        return f'{html}\n\n'

    def block_error(self, html):
        # TODO: this is non-standard. Maybe ignore?
        return f'<div class="error">{html}</div>\n\n'

    def list(self, text, ordered, level, start=None):
        if ordered:
            # convert `*` to `1.` in each list item using `start`.
            # TODO: make this increment. But how?
            start = f'{start}. ' if start is not None else '1. '
            text = UL_BULLET.sub(f'{start:<4}', text)
        if level == 1:
            # Adjust blank lines for level 1 lists
            # TODO: fix some edge cases with nested lists
            text = text.lstrip('\n')
            text += '\n\n'
        return text

    def list_item(self, text, level):
        global parse_success
        sequence_check_text = ""
        firstline = text
        if '\n' in text:
            # Indent all lines after the first line.
            firstline, therest = text.split('\n', 1)
            text = '\n'.join([firstline, indent(therest, 1)])
        # The linebreak goes at the front for nested items
        if self.check_begin:
            success, result = parse_info(firstline)
            if not success and not '\n' in text:
                sequence_check_text = fail(result)
                parse_success = False
            else:
                if level == self.lst_list_level:
                    sequence_check_text = ok("")
                    success, result = in_sequence(
                        self.lst_list_item, firstline)
                    if not success:
                        sequence_check_text = fail(result)
                        parse_success = False
                else:
                    sequence_check_text = ok("")
            self.lst_list_level = level
            self.lst_list_item = firstline

        x = text.split("\n")
        x[0] += sequence_check_text
        x = "\n".join(x)
        return f'\n*    {x}'


md2md = create_markdown(escape=False, renderer=MdRenderer())


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        src = f.read()
        print(md2md(src))
        if not parse_success:
            raise Error(fail("check failed, please refer to the above log"))
        else:
            print(ok("check success"))
