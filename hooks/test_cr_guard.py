"""Tests for cr-guard.sh.

Run after any change to the guard:  python3 hooks/test_cr_guard.py
Every line must say ok. Shells to test can be given as arguments; the default is sh, and bash when present.
"""
import json, subprocess, sys, time, os, tempfile, shutil

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cr-guard.sh")
WIN = r"D:\_Code\IPO-Debug_OfflinePack\.worktrees\vamos-2.0"


def hook(tool="Edit", path=None, key="file_path", agent=None, mode="default", content="x"):
    d = {"session_id": "s1", "transcript_path": r"C:\Users\grant\.claude\projects\p\s1.jsonl",
         "cwd": WIN, "permission_mode": mode, "hook_event_name": "PreToolUse",
         "tool_name": tool, "tool_input": {key: path, "content": content}, "tool_use_id": "t1"}
    if agent is not None:
        d["agent_id"] = agent
        d["agent_type"] = "cr-worker"
    return d


tricky = ('text that mentions "agent_id": "agent-fake" and "file_path": "WIP.md" and '
          '"permission_mode": "plan" and a path C:\\Users\\x\\.claude\\plans\\p.md')
edit_with_fake_keys = hook(path=WIN + r"\src\a.cs")
edit_with_fake_keys["tool_input"] = {"file_path": WIN + r"\src\a.cs",
                                     "old_string": '"file_path": "WIP.md"', "new_string": tricky}

D, A = "deny", "allow"
cases = [
    ("main edits a project source file (Windows path)", D, hook(path=WIN + r"\src\Nozzle\NozzleLife.cs"), {}),
    ("main writes a new project file (POSIX path)", D, hook("Write", "/home/u/proj/src/a.py"), {}),
    ("main NotebookEdit on a project notebook", D, hook("NotebookEdit", "/home/u/proj/nb.ipynb", key="notebook_path"), {}),
    ("worker (agent_id present) edits a project file", A, hook(path=WIN + r"\src\a.cs", agent="agent-abc123"), {}),
    ("worker in its worktree edits a file", A, hook(path=WIN + r"\.claude\worktrees\agent-x\src\a.cs", agent="agent-abc123"), {}),
    ("main writes WIP.md (Windows path)", A, hook("Write", WIN + r"\WIP.md"), {}),
    ("main writes CLAUDE.md", A, hook("Write", WIN + r"\CLAUDE.md"), {}),
    ("main writes docs/plan.md", A, hook("Write", WIN + r"\docs\plan.md"), {}),
    ("main writes docs/analysis/timing.md", A, hook("Write", "/home/u/proj/docs/analysis/timing.md"), {}),
    ("main edits docs/Helper.cs (code under docs)", D, hook(path="/home/u/proj/docs/Helper.cs"), {}),
    ("main edits README.md at project root", D, hook(path=WIN + r"\README.md"), {}),
    ("main appends to git's exclude file", A, hook(path=r"D:\_Code\IPO-Debug_OfflinePack\.git\info\exclude"), {}),
    ("main writes its plan file under ~/.claude/plans", A, hook("Write", r"C:\Users\grant\.claude\plans\calm-fox.md"), {}),
    ("main writes auto memory under ~/.claude/projects", A, hook("Write", r"C:\Users\grant\.claude\projects\p\memory\MEMORY.md"), {}),
    ("main edits a file inside a worker's worktree", D, hook(path=WIN + r"\.claude\worktrees\agent-x\src\a.cs"), {}),
    ("plan mode (any path)", A, hook("Write", WIN + r"\plans\x.md", mode="plan"), {}),
    ("main, content tries to look like agent_id/WIP.md/plan", D, hook("Write", WIN + r"\src\a.cs", content=tricky), {}),
    ("main, old_string/new_string contain a fake file_path key", D, edit_with_fake_keys, {}),
    ("main with agent_id null", D, dict(hook(path="/home/u/proj/a.py"), agent_id=None), {}),
    ("main with agent_id empty string", D, dict(hook(path="/home/u/proj/a.py"), agent_id=""), {}),
    ("main running as --agent (agent_type only, no agent_id)", D, dict(hook(path="/home/u/proj/a.py"), agent_type="something"), {}),
    ("CR_GUARD=off in the environment", A, hook(path=WIN + r"\src\a.cs"), {"CR_GUARD": "off"}),
    ("path with spaces and non-ASCII characters", D, hook(path="D:\\專案 資料\\機台 控制\\Main.cs"), {}),
    ("lower-case wip.md", A, hook("Write", "/home/u/proj/wip.md"), {}),
]


def run(argv, text, env):
    e = dict(os.environ)
    e.pop("CR_GUARD", None)
    e.update(env)
    t = time.time()
    p = subprocess.run(argv, input=text.encode("utf-8"), capture_output=True, env=e)
    out = p.stdout.decode("utf-8", "replace").strip()
    decision = A
    if out:
        decision = json.loads(out)["hookSpecificOutput"]["permissionDecision"]  # must be valid JSON
    return p.returncode, decision, out, time.time() - t


shells = sys.argv[1:] or [s for s in ("sh", "bash") if shutil.which(s)]
fails = 0
for shell in shells:
    print(f"\n===== {shell} =====")
    for name, want, payload, env in cases:
        bad = []
        for style, text in (("compact", json.dumps(payload, separators=(",", ":"), ensure_ascii=False)),
                            ("spaced", json.dumps(payload, ensure_ascii=False)),
                            ("ascii-escaped", json.dumps(payload, ensure_ascii=True)),
                            ("pretty", json.dumps(payload, indent=2, ensure_ascii=False))):
            rc, got, out, dt = run([shell, GUARD], text, env)
            if rc != 0 or got != want:
                bad.append(f"{style}: exit={rc} decision={got}")
        fails += len(bad)
        print(f"  {'FAIL' if bad else 'ok  '} {want:5}  {name}" + ("  <- " + "; ".join(bad) if bad else ""))
    for label, text in (("empty input", ""), ("garbage input", "not json at all"),
                        ("JSON without a path", json.dumps({"tool_name": "Edit", "tool_input": {}}))):
        rc, got, out, dt = run([shell, GUARD], text, {})
        ok = rc == 0 and got == A
        fails += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} allow  {label}")
    big = 'line of code with "quotes" and \\ backslashes\n' * 70000
    for label, payload, want in (("3 MB Write from main", hook("Write", WIN + r"\src\Big.cs", content=big), D),
                                 ("3 MB Write from a worker", hook("Write", WIN + r"\src\Big.cs", content=big, agent="agent-1"), A)):
        text = json.dumps(payload, separators=(",", ":"))
        rc, got, out, dt = run([shell, GUARD], text, {})
        ok = rc == 0 and got == want
        fails += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {want:5}  {label}: {len(text) / 1e6:.1f} MB in {dt * 1000:.0f} ms")

    # A damaged copy of the script (CRLF line endings, as a Windows checkout could produce) must not block anything.
    tmp = tempfile.mkdtemp(prefix="crlf_")
    crlf = os.path.join(tmp, "cr-guard.sh")
    open(crlf, "wb").write(open(GUARD, "rb").read().replace(b"\n", b"\r\n"))
    text = json.dumps(hook(path=WIN + r"\src\a.cs"))
    rc_raw, _, out_raw, _ = run([shell, crlf], text, {})
    rc_wrapped, got, out, _ = run([shell, "-c", f'sh "{crlf}" || true'], text, {})
    ok = rc_wrapped == 0 and got == A
    fails += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} allow  CRLF-damaged script run as `sh script || true` (raw exit code was {rc_raw}; wrapped exit={rc_wrapped}, stdout={out!r})")
    rc_wrapped, got, out, _ = run([shell, "-c", 'sh "/nonexistent/cr-guard.sh" || true'], text, {})
    ok = rc_wrapped == 0 and got == A
    fails += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} allow  missing script run as `sh script || true` (exit={rc_wrapped})")
    shutil.rmtree(tmp)

print("\nTOTAL FAILURES:", fails)
sys.exit(1 if fails else 0)
