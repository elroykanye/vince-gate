# Bindings

One JSON file per agent harness, describing how that harness wants the canonical skills on disk.
`scripts/install.py` reads these; there is no per-harness code.

See [`../docs/harnesses.md`](../docs/harnesses.md) for the field reference, the two layouts, the
frontmatter dialects, and how to add and honestly verify a new one.

```bash
python ../scripts/install.py bindings     # what is here, and its verification status
```

**`status` is a claim about reality.** `verified` means someone installed it into that runtime
and watched the skills be discovered and invoked. `unverified` means the paths follow the
runtime's documented convention and nothing more. Do not promote a binding without doing the
former — an overstated status costs the next person an afternoon of confusion.
