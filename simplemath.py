"""Render a small LaTeX subset into ReportLab's inline markup.

ReportLab has no maths engine. The articles in this family have historically
written their equations directly in its markup, which is fine until the same
prose has to serve both a KaTeX-rendered deck and a PDF. This converts the
subset actually used -- Greek letters, subscripts and superscripts, fractions,
roots and a handful of operators -- so that one source can feed both.
"""

import re

GREEK = {
    'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
    'epsilon': 'ε', 'varepsilon': 'ε', 'zeta': 'ζ',
    'eta': 'η', 'theta': 'θ', 'lambda': 'λ', 'mu': 'μ',
    'nu': 'ν', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ',
    'tau': 'τ', 'phi': 'φ', 'chi': 'χ', 'psi': 'ψ',
    'omega': 'ω', 'Delta': 'Δ', 'Omega': 'Ω',
    'Sigma': 'Σ', 'Phi': 'Φ', 'Gamma': 'Γ',
}
OPS = {
    r'\times': '×', r'\cdot': '·', r'\approx': '≈',
    r'\le': '≤', r'\ge': '≥', r'\neq': '≠', r'\pm': '±',
    r'\ll': '≪', r'\gg': '≫', r'\to': '→', r'\infty': '∞',
    r'\propto': '∝', r'\partial': '∂', r'\int': '∫',
    r'\sum': '∑', r'\,': ' ', r'\;': ' ', r'\!': '',
    r'\quad': ' ', r'\qquad': '  ', r'\ ': ' ',
}
FUNCS = ('ln', 'log', 'exp', 'sin', 'cos', 'tan', 'arctan', 'arcsin',
         'sinh', 'cosh', 'tanh', 'erfc', 'min', 'max')


def _braced(s, i):
    """Return (content, index_after) for a {...} group starting at s[i]=='{'."""
    depth, j = 0, i
    while j < len(s):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _frac(body):
    """\\frac{a}{b} and \\tfrac{a}{b} -> a/b, parenthesised when needed.

    Also accepts the braceless digit form \\tfrac12, which TeX allows and which
    is used for one-half often enough to be worth handling.
    """
    if body[:2].isdigit():
        return body[0] + '/' + body[1], 2
    num, k = _braced(body, 0)
    if k < len(body) and body[k] == '{':
        den, k2 = _braced(body, k)
        n = _tex(num); d = _tex(den)
        if len(n) > 1 and not n.isalnum():
            n = '(' + n + ')'
        if len(d) > 1 and not d.isalnum():
            d = '(' + d + ')'
        return n + '/' + d, k2
    return _tex(num), k


def _tex(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\':
            m = re.match(r'\\([A-Za-z]+)', s[i:])
            if m:
                name = m.group(1)
                j = i + m.end()
                if name in ('frac', 'tfrac', 'dfrac'):
                    txt, k = _frac(s[j:])
                    out.append(txt); i = j + k; continue
                if name == 'sqrt':
                    if j < len(s) and s[j] == '{':
                        inner, k = _braced(s, j)
                        out.append('√(' + _tex(inner) + ')'); i = k; continue
                    out.append('√'); i = j; continue
                if name in ('mathrm', 'text', 'mathbf', 'operatorname'):
                    # upright: these mark words, not single-letter variables
                    if j < len(s) and s[j] == '{':
                        inner, k = _braced(s, j)
                        out.append(re.sub(r'<i>(.*?)</i>', r'\1', _tex(inner)))
                        i = k; continue
                    i = j; continue
                if name in ('left', 'right', 'bigl', 'bigr'):
                    i = j; continue
                if name in GREEK:
                    out.append(GREEK[name]); i = j; continue
                if name in FUNCS:
                    out.append(name); i = j; continue
                key = '\\' + name
                if key in OPS:
                    out.append(OPS[key]); i = j; continue
                out.append(name); i = j; continue
            two = s[i:i + 2]
            if two in OPS:
                out.append(OPS[two]); i += 2; continue
            out.append(s[i + 1] if i + 1 < len(s) else '')
            i += 2; continue
        if c == '^' or c == '_':
            tag = 'super' if c == '^' else 'sub'
            j = i + 1
            if j < len(s) and s[j] == '{':
                inner, k = _braced(s, j)
                out.append('<%s>%s</%s>' % (tag, _tex(inner), tag)); i = k; continue
            if j < len(s):
                out.append('<%s>%s</%s>' % (tag, s[j], tag)); i = j + 1; continue
            i = j; continue
        if c == '-':
            out.append('−'); i += 1; continue
        if c.isalpha():
            m = re.match(r'[A-Za-z]+', s[i:])
            word = m.group(0)
            if word in FUNCS:
                out.append(word)
            elif len(word) == 1:
                out.append('<i>%s</i>' % word)
            else:
                out.append('<i>%s</i>' % word)
            i += len(word); continue
        out.append(c); i += 1
    return ''.join(out)


def M(text):
    """Convert every $...$ span in `text` to ReportLab inline markup."""
    def repl(m):
        return _tex(m.group(1))
    return re.sub(r'\$\$(.+?)\$\$', repl, re.sub(r'(?<!\$)\$([^$]+)\$', repl, text),
                  flags=re.S)
