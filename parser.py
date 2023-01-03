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


def parse_toc(line):
    x = re.search(r"\[(.*?)(?: \(原 (?:.*?)\))?: (.*?)\]\(#(.*?)\)", line)
    if not x:
        return False, f"failed to parse: no [ID, course name](#anchor) found"
    course_id, course_name, anchor = x.group(1), x.group(2), x.group(3)
    real_course_id = course_id.split(", ")[0]
    if real_course_id.lower() != anchor.lower():
        return False, f"failed to parse: unmatched course id and anchor"
    if course_id != course_id.upper():
        return False, f"failed to parse: please use upper case in course ID"
    if anchor != anchor.lower():
        return False, f"failed to parse: please use lower case in URL anchor"
    return True, (real_course_id, course_name)


def in_toc_sequence(a, b):
    success_a, result_a = parse_toc(a)
    success_b, result_b = parse_toc(b)
    if not success_a:
        return False, f"previous line is broken"
    if not success_b:
        return False, result_b
    course_id_a, _ = result_a
    course_id_b, _ = result_b
    if course_id_a > course_id_b:
        return False, f"course ID not in sequence"
    return True, None


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


def parse_anchor(line):
    x = re.search(r"name=\"(.*?)\"", line)
    if x:
        return x.group(1)
    else:
        return None


def fail(text):
    global parse_success
    parse_success = False
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
        self.content_check = False
        self.first_toc = True
        self.toc = []
        self.last_html = ""

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
        self.last_html += html
        return html

    def paragraph(self, text):
        return f'{text}\n\n'

    def heading(self, text, level):
        append_text = ""
        prepend_text = ""
        if level == 3:
            result = re.match(r"(.*)(?: \(原 (?:.*)\))? - (.*)", text)
            if result:
                anchor = parse_anchor(self.last_html)
                self.last_html = ""
                course_id = result.group(1).split(" + ")[0]
                if not anchor:
                    prepend_text = fail(f"no anchor found") + "\n"
                elif anchor.lower() != course_id.lower():
                    prepend_text = fail(f"anchor not match: {anchor}") + "\n"
                if self.toc:
                    result = [(i, toc) for i, toc in enumerate(
                        self.toc) if toc[0] == course_id]
                    if not result:
                        append_text = fail("item not in TOC")
                    else:
                        i, toc = result[0]
                        if i != 0:
                            prepend_text += fail(
                                f"missing item: {self.toc[:i]}") + "\n"
                            append_text = ok("")
                            self.toc = self.toc[i+1:]
                        else:
                            append_text = ok("")
                            self.toc = self.toc[i+1:]
                else:
                    append_text = fail("item not in TOC")
                self.check_begin = True
                self.lst_list_item = ""
                self.lst_list_level = 0
            else:
                self.check_begin = False
            if text == "目录":
                append_text = ok("table of contents")
                self.content_check = True
            else:
                self.content_check = False

        return f'{prepend_text}{"#"*level} {text}{append_text}\n\n'

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
            else:
                if level == self.lst_list_level:
                    sequence_check_text = ok("")
                    success, result = in_sequence(
                        self.lst_list_item, firstline)
                    if not success:
                        sequence_check_text = fail(result)
                else:
                    sequence_check_text = ok("")
            self.lst_list_level = level
            self.lst_list_item = firstline

        if self.content_check:
            success, result = parse_toc(firstline)
            if not success:
                sequence_check_text = fail(result)
            else:
                self.toc.append(result)
                sequence_check_text = ok("")
                if not self.first_toc:
                    success, result = in_toc_sequence(
                        self.lst_list_item, firstline)
                    if not success:
                        sequence_check_text = fail(result)
                self.lst_list_item = firstline
                self.first_toc = False

        x = text.split("\n")
        x[0] += sequence_check_text
        x = "\n".join(x)
        return f'\n*    {x}'


renderer = MdRenderer()
md2md = create_markdown(escape=False, renderer=renderer)


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        src = f.read()
        print(md2md(src))
        if renderer.toc:
            print(fail(f"missing items: {renderer.toc}"))
        if not parse_success:
            raise Error(fail("check failed, please refer to the above log"))
        else:
            print(ok("check success"))
