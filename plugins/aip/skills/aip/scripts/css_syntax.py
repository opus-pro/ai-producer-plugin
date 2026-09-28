"""Find the stylesheet errors that the export's strict CSS parser refuses.

A browser recovers from malformed CSS by dropping what it cannot read, so a stylesheet with a
stray brace, a missing semicolon, or a cut-off rule previews normally. The export compiles
every stylesheet with a strict parser that stops at the first such error, and the export fails
before any frame renders. This mirrors that parser's structural rules and reports only what it
refuses: a stylesheet that passes here can still style the page wrongly.
"""

import re

_CLOSERS = {"(": ")", "[": "]"}
_TRAILING_WORD = re.compile(r"[\w-]*$")
_SECOND_WORD = re.compile(r"\s*\S+\s+(?=\S)")
_WORD_START = re.compile(r"[^\s{}();:\[\]'\"/\\,!]")
# A `(` right after `url` and before any of these opens a quoted or spaced url(), which the
# parser tokenizes normally; any other `url(` it reads raw up to the closing `)`.
_NOT_RAW_URL = ("", "'", '"', " ", "\n", "\t", "\f", "\r")


def first_error(css):
    """``(offset, reason)`` for the first error the strict parser refuses in ``css``, or None."""
    return _Scanner(css).run()


def position(css, offset):
    """1-based ``(line, column)`` of ``offset`` in ``css``."""
    return css.count("\n", 0, offset) + 1, offset - css.rfind("\n", 0, offset)


def _unescaped(css, char, start):
    """Offset of the next ``char`` after ``start`` that no backslash escapes, or -1."""
    end = start
    while True:
        end = css.find(char, end + 1)
        if end < 0:
            return -1
        backslashes = 0
        while end - backslashes - 1 > start and css[end - backslashes - 1] == "\\":
            backslashes += 1
        if backslashes % 2 == 0:
            return end


class _Scanner:
    """One pass over a stylesheet, split into statements the way the parser splits them: a
    statement ends at `{` (a selector or at-rule prelude), `;`, or `}` outside any bracket.
    Comments are dropped; strings, escapes, and a raw `url(...)` are opaque."""

    def __init__(self, css):
        self.css = css
        self.blocks = []
        self.brackets = []
        self.reset()

    def reset(self):
        self.chars = []
        self.offsets = []
        self.colons = []

    def take(self, start, end):
        self.chars.extend(self.css[start:end])
        self.offsets.extend(range(start, end))

    def text(self):
        return "".join(self.chars)

    def run(self):
        css, i = self.css, 0
        while i < len(css):
            char = css[i]
            if css.startswith("/*", i):
                end = css.find("*/", i + 2)
                if end < 0:
                    return i, "Unclosed comment"
                i = end + 2
                continue
            opaque = self.opaque(char, i)
            if opaque:
                end = _unescaped(css, opaque[0], i)
                if end < 0:
                    return i, opaque[1]
                self.take(i, end + 1)
                i = end + 1
                continue
            if char == "\\":
                self.take(i, i + 2)
                i += 2
                continue
            error = self.structural(char, i)
            if error:
                return error
            i += 1
        return self.finish()

    def opaque(self, char, offset):
        """``(closer, reason if unclosed)`` when ``char`` opens a span read whole: a string, or
        an unquoted `url(` the parser reads raw up to its `)`. None otherwise."""
        if char in "\"'":
            return char, "Unclosed string"
        # Four characters are enough: a longer word ending in `url` has a word character there.
        if char == "(" and _TRAILING_WORD.search("".join(self.chars[-4:])).group(0) == "url":
            if self.css[offset + 1:offset + 2] not in _NOT_RAW_URL:
                return ")", "Unclosed bracket"
        return None

    def structural(self, char, offset):
        if self.brackets:
            if char in _CLOSERS:
                self.brackets.append((_CLOSERS[char], offset))
            elif char == self.brackets[-1][0]:
                self.brackets.pop()
        elif char in _CLOSERS:
            self.brackets.append((_CLOSERS[char], offset))
        elif char == "{" and self.colons and self.text().lstrip().startswith("--"):
            # A custom property's value may hold a block, so its brace opens a bracket.
            self.brackets.append(("}", offset))
        elif char == "{":
            self.reset()
            self.blocks.append(offset)
            return None
        elif char in ";}":
            error = self.end_statement()
            if error or char == ";":
                return error
            if not self.blocks:
                return offset, "Unexpected }"
            self.blocks.pop()
            return None
        elif char == ":":
            self.colons.append(len(self.chars))
        self.take(offset, offset + 1)
        return None

    def end_statement(self):
        text, offsets, colons = self.text(), self.offsets, self.colons
        self.reset()
        body = text.lstrip()
        # An empty statement and an at-rule never fail here: the parser reads an at-rule's
        # parameters without judging them.
        if not body or body.startswith("@"):
            return None
        if not colons:
            return offsets[len(text) - len(body)], "Unknown word"
        # The parser moves leading colons into the declaration's preamble. A statement that
        # opens with any other punctuation takes paths this check does not model, so it is
        # left to the parser rather than guessed at.
        lead = len(text) - len(text.lstrip(": \t\n\r\f"))
        if lead == len(text) or not _WORD_START.match(text, lead):
            return None
        colons = [colon for colon in colons if colon >= lead]
        if not colons:
            return offsets[lead], "Unknown word"
        text, offsets = text[lead:], offsets[lead:]
        colons = [colon - lead for colon in colons]
        first = colons[0]
        # The property is one word; a second word before the colon is not part of it.
        second_word = _SECOND_WORD.match(text[:first])
        if second_word and re.search(r"\w", text[second_word.end():first]):
            return offsets[second_word.end()], "Unknown word"
        if text.startswith("--"):
            return None
        if text[first + 1:].lstrip().startswith(":"):
            return offsets[colons[1]], "Double colon"
        for colon in colons[1:]:
            word = _TRAILING_WORD.search(text, 0, colon).group(0)
            if word != "progid":
                return offsets[colon - len(word)], "Missed semicolon"
        return None

    def finish(self):
        if self.brackets and not self.text().lstrip().startswith("@"):
            return self.brackets[0][1], "Unclosed bracket"
        error = self.end_statement()
        if error:
            return error
        if self.blocks:
            return self.blocks[-1], "Unclosed block"
        return None
