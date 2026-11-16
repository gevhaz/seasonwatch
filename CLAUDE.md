# Code style

- Use very descriptive variable names, even if they're long.
- Don't cram logic into one line. Prefer a plain loop or a named
  variable over a dense comprehension or a long expression.
- Follow PEP 8 and PEP 257 and write idiomatic Python, e.g. plain
  functions in a module rather than a class of static methods. Where
  the rules here differ from them, the rules here win.

# Docstrings

- Write for the caller: give enough to call the function without
  reading its code. Say what it returns, or what it does if it's
  called for its effect, and the special cases and constraints that
  its name and signature don't show.
- Don't restate the signature, e.g. `:param title: The title.` Leave
  out the parameter and return sections when a sentence covers them.
- Use a single line when the name and signature say the rest. An
  example often says more than another sentence would.
- Explain how the function works in comments in its body, so that the
  docstring stays true when the implementation changes. Leave out
  background that the caller doesn't need.
- Whatever a docstring repeats from the code has to be kept in sync by
  hand, and no check notices when it isn't. Prefer saying less to
  saying something that can go stale.
- Shorter doesn't mean fewer: public functions and functions with
  non-obvious behavior still get a docstring.

# Platforms

- Only Linux is supported, so e.g. libnotify and XDG paths can be used
  without a fallback for other platforms.

# Spellcheck

- Keep the words in `.github/data/project-dictionary.txt` sorted
  alphabetically, with uppercase before lowercase.

# Writing

- Write pull request descriptions and commit messages for a reader who
  reads them first, to get oriented, and only then looks at the code.
  Don't assume they already have a specific part of the code in mind.

# Commits

- Write the subject in the imperative mood, capitalized, without a full
  stop and without prefixes like `feat:`, e.g. "Fix parsing of air
  dates". Keep it short, ideally under 50 characters.
- In the body, explain what's wrong without the change and why the
  change fixes it. The diff shows how.
- Keep commit messages as long as the change needs, and only a little
  longer than in code written without AI. A small change gets a subject
  line and at most a few lines of body.
- Make one commit per logical change, e.g. a refactoring, a bug fix and
  a new feature are separate commits. One change across many files is
  still one commit. Each commit should pass the checks on its own.
- Until a branch is merged, fold review fixes into the commits they fix.

# Pull requests

- Start the description with the problem, then explain why the change
  fixes it.
- Link the issues it fixes with a closing keyword, e.g. "Closes #84",
  so they're closed when the pull request is merged.
- When the change shows in the terminal, show it with a few lines of
  real output.
- Name the decisions and trade-offs, and the cases the change still
  doesn't handle.
- Mention checks done by hand that CI doesn't repeat, e.g. checking
  that a desktop notification shows up. Don't mention the automated
  ones.
- Leave out what the diff, the commit list or CI already shows, e.g.
  that the checks pass, a summary of each commit, or a list of renamed
  and removed functions.
- Keep the description in proportion to the change. A small fix gets a
  few sentences.
- Write in prose. Use headings only when the description is long enough
  that a reader needs to skip to a part.
