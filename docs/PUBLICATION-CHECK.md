# Publication input check

Run `python tools/check_publication_inputs.py` from this repository before uploading.
It checks tracked files for known binary/backup paths, private-key PEM headers and
Dangol owner-backup receipt structure without printing suspect contents or paths.
GitHub Actions runs it too, but that occurs **after** a push: it cannot prevent or
remove secrets already uploaded. Review the exact staged files before publishing.

This is not a complete detector for encoded/compressed secrets, arbitrary tokens,
owner MAC addresses, historical commits or Release assets. Passing does not establish
privacy, licensing clearance or permission to publish a ROM.
