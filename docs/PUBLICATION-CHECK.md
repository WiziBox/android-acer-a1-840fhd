# Publication input check

Run `python tools/check_publication_inputs.py` from this repository before uploading.
It checks tracked files for known binary/backup paths, private-key PEM headers and
known private owner-backup receipt structures without printing suspect contents or paths.
GitHub Actions runs it too, but that occurs **after** a push: it cannot prevent or
remove secrets already uploaded. Review the exact staged files before publishing.

This is not a complete detector for encoded/compressed secrets, arbitrary tokens,
owner MAC addresses, historical commits or Release assets. Passing does not establish
privacy, licensing clearance or permission to publish a ROM.

After `git add`, run `python tools/check_publication_inputs.py --staged` before committing.
This checks actual added/modified index blobs, not their working-copy replacements.
A secret left staged is detected even if the working file was subsequently cleaned.
Deleted files are excluded; symlinks, submodules and conflicts are refused. Re-run after
any index changes. Also run the default whole tracked working-tree check.
