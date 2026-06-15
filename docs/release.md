# Release Checklist

TNView is still alpha. Use this checklist before tagging a release.

1. Run local verification:

   ```bash
   make check
   make runlog-demo
   .venv/bin/python -m pip install -e .
   ```

2. Confirm the CLI entry point:

   ```bash
   tnview --help
   tnview tail examples/quimb_tnoptimizer_run.jsonl
   tnview diagnose examples/dmrg_bad_run.jsonl
   ```

3. Confirm GitHub Actions is green on `main`.

4. Update version strings:

   - `pyproject.toml`
   - `tnview/__init__.py`
   - `CHANGELOG.md`

5. Build the package from a clean tree:

   ```bash
   python -m build
   ```

6. Inspect artifacts:

   ```bash
   python -m twine check dist/*
   ```

7. Tag after verification:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
