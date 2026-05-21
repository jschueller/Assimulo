"""
Preprocessor to resolve Cython IF/ELIF/ELSE compile-time conditionals.

Replaces deprecated Cython 'IF' statements with their evaluated branches.
Each IF chain is replaced by the body of the selected branch, with proper
de-indentation (bodies are indented one level deeper than the IF directive).
"""

import os


def _eval(expr, env):
    try:
        return bool(eval(expr, env))
    except Exception:
        return False


def _indent(line):
    content = line.rstrip('\n\r')
    return len(content) - len(content.lstrip())


def find_branch_end(lines, body_start, end, if_indent):
    """Find where a branch body ends (when a non-blank line's indent returns
    to if_indent or less).  Blank lines are skipped since they don't carry
    meaningful indentation."""
    i = body_start
    while i < end:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if _indent(lines[i]) <= if_indent:
            break
        i += 1
    return i


def parse_if_chain(lines, start, end):
    """Parse an IF chain and return (branches, chain_end)."""
    if_indent = _indent(lines[start])
    branches = []
    i = start

    while i < end:
        stripped = lines[i].lstrip()
        indent = _indent(lines[i])

        if indent < if_indent:
            break
        if indent > if_indent:
            i += 1
            continue

        if stripped.startswith("IF "):
            if branches:
                break  # new IF chain starts; current chain is done
            cond = stripped[3:].rstrip(":\n").strip()
            body_start = i + 1
            body_end = find_branch_end(lines, body_start, end, if_indent)
            branches.append(("if", cond, body_start, body_end))
            i = body_end
        elif stripped.startswith("ELIF "):
            cond = stripped[5:].rstrip(":\n").strip()
            body_start = i + 1
            body_end = find_branch_end(lines, body_start, end, if_indent)
            branches.append(("elif", cond, body_start, body_end))
            i = body_end
        elif stripped.rstrip() == "ELSE:":
            body_start = i + 1
            body_end = find_branch_end(lines, body_start, end, if_indent)
            branches.append(("else", None, body_start, body_end))
            i = body_end
            break
        else:
            break

    return branches, i


def select_branch(branches, env):
    """Return (body_start, body_end) of the selected branch, or None."""
    for typ, cond, bs, be in branches:
        if typ == "else" or (cond is not None and _eval(cond, env)):
            return bs, be
    return None


def process_body(lines, start, end, target_indent, env):
    """Process body lines and output at target_indent.

    Body lines are expected at target_indent + 4 (or deeper).  They are
    de-indented by 4.  Nested IF chains are resolved recursively.
    """
    result = []
    i = start
    while i < end:
        line = lines[i]
        indent = _indent(line)

        if indent < target_indent:
            break

        stripped = line.lstrip()
        if stripped.startswith("IF "):
            # Nested IF chain
            branches, chain_end = parse_if_chain(lines, i, end)
            sel = select_branch(branches, env)
            if sel is not None:
                bs, be = sel
                processed = process_body(lines, bs, be, indent, env)
                # De-indent the nested chain output by 4 (relative to outer body)
                for p in processed:
                    result.append(p[4:] if len(p) > 4 else p)
            i = chain_end
            continue

        # Regular body line: de-indent by 4
        result.append(line[4:] if len(line) > 4 else line)
        i += 1

    return result


def process_top(lines, start, end, env):
    """Process top-level file content, resolving IF chains at any indent level."""
    result = []
    i = start
    while i < end:
        line = lines[i]
        stripped = line.lstrip()
        if_indent = _indent(line)

        if stripped.startswith("IF "):
            branches, chain_end = parse_if_chain(lines, i, end)
            sel = select_branch(branches, env)
            if sel is not None:
                bs, be = sel
                processed = process_body(lines, bs, be, if_indent, env)
                result.extend(processed)
            i = chain_end
        else:
            result.append(line)
            i += 1
    return result


def _substitute_env_vars(content, env):
    """Replace compile-time env var references with their literal values.

    The Cython compile-time environment variables (SUNDIALS_VERSION etc.)
    are also referenced outside IF/ELIF/ELSE directives (e.g.
    ``_sundials_version = SUNDIALS_VERSION``).  After the IF preprocessor
    has run, these bare names must be replaced with their actual values.
    """
    for name, value in sorted(env.items(), key=lambda x: -len(x[0])):
        # Build the replacement string.  Tuples become (6,0,0), booleans
        # become True/False, strings remain quoted.
        if isinstance(value, tuple):
            replacement = str(value)
        elif isinstance(value, bool):
            replacement = "True" if value else "False"
        elif isinstance(value, str):
            replacement = value
        else:
            replacement = str(value)
        content = content.replace(name, replacement)
    return content


def preprocess_file(source_path, env):
    """Resolve IF/ELIF/ELSE blocks in a Cython source file in-place."""
    with open(source_path) as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    if not lines:
        return

    result = process_top(lines, 0, len(lines), env)
    output = "".join(result)
    output = _substitute_env_vars(output, env)

    with open(source_path, "w") as f:
        f.write(output)


def preprocess_directory(root_dir, env, extensions=(".pyx", ".pxd", ".pxi")):
    """Recursively preprocess all matching files under root_dir."""
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.endswith(extensions):
                path = os.path.join(dirpath, fn)
                preprocess_file(path, env)
