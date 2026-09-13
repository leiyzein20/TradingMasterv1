#!/usr/bin/env python3
"""Static checks for Pine v6 that the editor only reports one error at a time."""
import re, sys, collections

path = sys.argv[1]
src = open(path).read()
lines = src.split("\n")

problems = []

def strip_str(s):
    out, i, q = [], 0, None
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 2; continue
            if c == q:
                q = None
            out.append(" ")
        else:
            if c in "\"'":
                q = c; out.append(" ")
            elif c == "/" and i + 1 < len(s) and s[i+1] == "/":
                break
            else:
                out.append(c)
        i += 1
    return "".join(out)

code = [strip_str(l) for l in lines]

# ---------- 1. declaration statements ----------
decls = [i for i, l in enumerate(code)
         if re.match(r"^(indicator|strategy|library)\s*\(", l)]
if len(decls) != 1:
    problems.append(("CE10243", f"{len(decls)} declaration statements at lines "
                                f"{[d+1 for d in decls]}"))

# ---------- 2. delimiter balance ----------
depth = 0
for i, l in enumerate(code):
    depth += l.count("(") + l.count("[") - l.count(")") - l.count("]")
    if depth < 0:
        problems.append(("PAREN", f"line {i+1}: closes more than it opens"))
        depth = 0
if depth != 0:
    problems.append(("PAREN", f"file ends with {depth} unclosed delimiters"))

# ---------- 3. continuation-line indent ----------
# Pine treats an indent that is a multiple of 4 as a new block, not a
# continuation. Continuation lines must be indented by a non-multiple of 4.
depth = 0
for i, l in enumerate(code):
    if depth > 0 and lines[i].strip():
        ind = len(lines[i]) - len(lines[i].lstrip())
        if ind % 4 == 0 and ind > 0:
            problems.append(("INDENT", f"line {i+1}: continuation indented {ind} "
                                       f"(multiple of 4) — Pine reads a new block"))
    depth += l.count("(") + l.count("[") - l.count(")") - l.count("]")
    depth = max(depth, 0)

# ---------- 4. ta.* inside a ternary branch ----------
# A ta.* call in a conditional branch only advances its state on bars where the
# branch is taken, which silently corrupts the series.
for i, l in enumerate(code):
    if "?" in l and re.search(r"\bta\.", l):
        after = l.split("?", 1)[1]
        if re.search(r"\bta\.(ema|sma|rma|atr|rsi|highest|lowest|stdev|percentrank|"
                     r"pivothigh|pivotlow|change|sum|vwap|macd|crossover|crossunder)\b",
                     after):
            problems.append(("TA-TERNARY", f"line {i+1}: {lines[i].strip()[:80]}"))

# ---------- 5. declarations and forward references ----------
decl_line = {}
func_line = {}
for i, l in enumerate(code):
    m = re.match(r"^(\w+)\s*\(([^)]*)\)\s*=>", l)
    if m:
        func_line.setdefault(m.group(1), i)
        continue
    m = re.match(r"^(?:var\s+)?(?:int|float|bool|string|color|line|label|box|table|array<[^>]+>)?\s*(\w+)\s*=(?!=|>)", l)
    if m:
        decl_line.setdefault(m.group(1), i)
    m = re.match(r"^\[([^\]]+)\]\s*=", l)
    if m:
        for name in m.group(1).split(","):
            decl_line.setdefault(name.strip(), i)

KEYWORDS = set("""if else for while and or not na nz true false var varip import export type
switch input indicator strategy library plot plotshape plotchar bgcolor fill alertcondition
alert barcolor hline line label box table color math str array ta request syminfo timeframe
barstate close open high low volume hl2 hlc3 ohlc4 time bar_index format size shape location
xloc yloc text style int float bool string series simple const method to by in continue break
plotarrow plotcandle extend xloc yloc order position scale display currency dayofweek
session adjustment matrix map runtime log chart font math str request timeframe syminfo
barstate strategy input""".split())

# global identifiers used before their declaration line, including inside
# function bodies (the gap that let CE10272 through last time)
body_owner = None
call_depth = 0
for i, l in enumerate(code):
    stripped = l.strip()
    if not stripped or stripped.startswith("//"):
        continue
    m = re.match(r"^(\w+)\s*\(([^)]*)\)\s*=>", l)
    if m:
        body_owner = (m.group(1), i, set(p.strip().split()[-1]
                                         for p in m.group(2).split(",") if p.strip()))
        continue
    indented = l.startswith(" ") or l.startswith("\t")
    if body_owner and not indented:
        body_owner = None
    ref_line = body_owner[1] if body_owner else i
    locals_ = body_owner[2] if body_owner else set()
    rhs = l.split("=", 1)[1] if re.match(r"^\s*[\w\[\]., ]+=(?!=)", l) else l
    # Named arguments (extend = ..., text_size = ...) are parameter names, not
    # references to anything, so they must not be read as forward references.
    if "(" in rhs or call_depth > 0:
        rhs = re.sub(r"[\w.]+\s*=(?!=)", " ", rhs)
    call_depth = max(0, call_depth + l.count("(") + l.count("[")
                        - l.count(")") - l.count("]"))
    for name in re.findall(r"\b[a-zA-Z_]\w*\b", rhs):
        if name in KEYWORDS or name in locals_:
            continue
        d = decl_line.get(name)
        f = func_line.get(name)
        src_line = d if d is not None else f
        if src_line is not None and src_line > ref_line:
            problems.append(("CE10272", f"line {i+1}: '{name}' used"
                                        + (f" in {body_owner[0]}()" if body_owner else "")
                                        + f" before its declaration on line {src_line+1}"))

# ---------- 6. name collisions between a function and a variable ----------
for name in set(func_line) & set(decl_line):
    problems.append(("COLLISION", f"'{name}' is both a function (line "
                                  f"{func_line[name]+1}) and a variable (line "
                                  f"{decl_line[name]+1})"))

# ---------- 8. built-in namespace members actually exist ----------
# The compiler reports one of these at a time and only once you paste. ta.sum
# is the classic trap: it was sum() in v4 and became math.sum in v5, so the
# wrong namespace looks completely plausible.
NS = {
 "ta": """alma atr barssince bb bbw cci change cmo cog correlation cross crossover
 crossunder cum dev dmi ema falling highest highestbars hma kc kcw linreg lowest
 lowestbars macd max median mfi min mode mom percentile_linear_interpolation
 percentile_nearest_rank percentrank pivot_point_levels pivothigh pivotlow range
 rising rma roc rsi sar sma stdev stoch supertrend swma tr tsi valuewhen variance
 vwap vwma wma wpr""",
 "math": """abs acos asin atan avg ceil cos e exp floor log log10 max min phi pi pow
 random round round_to_mintick rphi sign sin sqrt sum tan todegrees toradians""",
 "str": """contains endswith format format_time length lower match pos repeat replace
 replace_all split startswith substring tonumber tostring trim upper""",
 "box": """new copy delete get_bottom get_left get_right get_top set_bgcolor
 set_border_color set_border_style set_border_width set_bottom set_bottom_right_point
 set_extend set_left set_lefttop set_right set_rightbottom set_text set_text_color
 set_text_font_family set_text_halign set_text_size set_text_valign set_text_wrap
 set_top set_top_left_point all
 style_solid style_dotted style_dashed""",
 "line": """new copy delete get_price get_x1 get_x2 get_y1 get_y2 set_color set_extend
 set_first_point set_second_point set_style set_width set_x1 set_x2 set_xloc set_xy1
 set_xy2 set_y1 set_y2 all
 style_solid style_dotted style_dashed style_arrow_left style_arrow_right
 style_arrow_both""",
 "label": """new copy delete get_text get_x get_y set_color set_size set_style set_text
 set_textalign set_textcolor set_text_font_family set_tooltip set_x set_xloc set_xy
 set_y set_yloc all
 style_none style_xcross style_cross style_triangleup style_triangledown style_flag
 style_circle style_arrowup style_arrowdown style_label_up style_label_down
 style_label_left style_label_right style_label_lower_left style_label_lower_right
 style_label_upper_left style_label_upper_right style_label_center style_square
 style_diamond style_text_outline""",
 "table": """new cell cell_set_bgcolor cell_set_height cell_set_text cell_set_text_color
 cell_set_text_font_family cell_set_text_halign cell_set_text_size cell_set_text_valign
 cell_set_tooltip cell_set_width clear delete merge_cells set_bgcolor set_border_color
 set_border_width set_frame_color set_frame_width set_position all""",
 "request": """security security_lower_tf currency_rate dividends earnings economic
 financial quandl seed splits""",
}
NS = {k: set(v.split()) for k, v in NS.items()}
for i, l in enumerate(code):
    for ns, member in re.findall(r"\b(ta|math|str|box|line|label|table|request)\.(\w+)", l):
        if member not in NS[ns]:
            problems.append(("NO-SUCH-FN", f"line {i+1}: '{ns}.{member}' is not a "
                                           f"Pine v6 built-in"))

# ---------- 9. a name declared twice at top level ----------
# Pine has no shadowing at global scope: a second `x = ...` is a redeclaration
# error, and it is easy to hit when a tuple destructuring reuses a short name
# that the palette or the inputs already took (cE20 as both a colour and an
# EMA value, for instance). Counts tuple targets as declarations too.
seen = {}
for i, l in enumerate(code):
    names = []
    m = re.match(r"^(?:var(?:ip)?\s+)?(?:(?:int|float|bool|string|color|line|label|box|table|array<[^>]+>)\s+)?(\w+)\s*=(?!=)", l)
    if m:
        names.append(m.group(1))
    m = re.match(r"^\[([^\]]+)\]\s*=", l)
    if m:
        names += [n.strip().split()[-1] for n in m.group(1).split(",") if n.strip()]
    for n in names:
        if n in seen:
            problems.append(("REDECLARED", f"line {i+1}: '{n}' was already "
                                           f"declared on line {seen[n]+1}"))
        else:
            seen[n] = i

# ---------- 10. if / else branches with clashing return types ----------
# CE10235. A block's type is the type of its LAST statement. array.shift,
# array.pop and array.remove RETURN the element they removed, so a branch
# ending in one is typed float/int while a sibling ending in array.push or
# array.set is void — and Pine refuses to reconcile them. This is invisible
# while reading because both lines look like the same kind of housekeeping.
VALUE_FN = re.compile(r"^(?:array|matrix|map)\.(shift|pop|remove|get|size|"
                      r"indexof|lastindexof|includes|join|slice|copy|sum|avg|"
                      r"min|max|median|mode|stdev|variance|range|first|last)\s*\(")
VOID_FN = re.compile(r"^(?:(?:array|matrix|map)\.(?:push|set|unshift|insert|clear|"
                     r"fill|sort|reverse|concat)|(?:label|line|box|table|linefill|"
                     r"polyline)\.(?:delete|set_\w+|cell\w*)|\w+\s*:=)\s*\(?")

def kind(stmt):
    t = stmt.strip()
    if not t or t.startswith("//"):
        return None
    if VALUE_FN.match(t):
        return "value"
    if VOID_FN.match(t) or re.match(r"^\w+\s*:=", t):
        return "void"
    return None

def indent_of(k):
    return len(lines[k]) - len(lines[k].lstrip())

def last_stmt_kind(start, end, base):
    """Kind of the deepest last executable statement of a branch body."""
    last = None
    for k in range(start, end):
        if not code[k].strip() or lines[k].lstrip().startswith("//"):
            continue
        if indent_of(k) <= base:
            break
        last = k
    return (kind(code[last]), last + 1) if last is not None else (None, None)

for i, l in enumerate(code):
    m = re.match(r"^(\s*)if\s+\S", l)
    if not m:
        continue
    base = len(m.group(1))
    # find the matching else at the same indent
    j = i + 1
    else_at = None
    while j < len(code):
        if code[j].strip() and indent_of(j) <= base:
            if re.match(r"^\s*else\b", code[j]) and indent_of(j) == base:
                else_at = j
            break
        j += 1
    if else_at is None:
        continue
    k1, ln1 = last_stmt_kind(i + 1, else_at, base)
    end = else_at + 1
    while end < len(code) and (not code[end].strip() or indent_of(end) > base):
        end += 1
    k2, ln2 = last_stmt_kind(else_at + 1, end, base)
    if k1 and k2 and k1 != k2:
        problems.append(("CE10235", f"line {i+1}: if/else branches end in "
                                    f"different types — line {ln1} is {k1}, "
                                    f"line {ln2} is {k2}"))

# ---------- 7. token estimate ----------
raw = sum(len(re.findall(r"[A-Za-z_]\w*|\d+\.?\d*|[^\s\w]", l)) for l in code)
est = int(raw * 5.18)
print(f"lines            {len(lines)}")
print(f"raw tokens       {raw}")
print(f"compiler est.    {est:,}  (limit 100,256)"
      + ("  ⚠ OVER" if est > 100256 else "  ok"))
print(f"declarations     {len(decls)}")
print()

if problems:
    by = collections.Counter(p[0] for p in problems)
    print("PROBLEMS:", dict(by))
    for kind, msg in problems[:60]:
        print(f"  [{kind}] {msg}")
    sys.exit(1)
print("no structural problems found")
