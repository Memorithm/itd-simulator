# Release integrity

Verified on 2026-07-19 against Git tags, repository history, and public GitHub
release assets.

| Scientific revision | Software version | Git tag | Commit | Artifact | Artifact SHA-256 | Manifest file SHA-256 |
|---|---:|---|---|---|---|---|
| V10 | 0.1.1 | `v0.1.1` | `478f812f5abb1ea9c6e9be3e04a623d7d11d2b8e` | `itd-simulator-0.1.1.tar.gz` (public GitHub release asset) | `af323367f804853ebf980e0805d2127714b7f5971abb3d0848d375b4931ba00e` | not present in the archive |
| ITD V29.18 | historical scientific snapshot | `v29.18` | `4896cac9f312e0008ecf5c78058f9e1508a392f2` | no GitHub release artifact | not applicable | `139d20a0f12225d821c1b91b44cf5d67fdfea111ad4e21d0f15e9b6b3776efca` |
| ITD V29.18 | 0.2.0 source tree | pending review | pending merge | no public artifact | not applicable | generated and verified in the source tree; publication value pending merge |

The V10 archive SHA in earlier README versions was correct but lacked an
artifact name and version context. It does not hash V29 source. Its detached
`.sha256` release asset agrees with the locally downloaded archive.

The `v29.18` row hashes the contents of `MANIFEST.sha256` at that tag; it is not
an archive hash. GitHub has no release object or downloadable V29.18 archive
asset corresponding to that scientific tag.

## Current manifest contract

`MANIFEST.sha256` is canonical, sorted, duplicate-free, and covers every
tracked regular file except itself. `python tools/check_manifest.py` validates
syntax, path safety, scope, ordering, and file digests. Updating it is an
explicit maintainer action:

```bash
python tools/check_manifest.py --update
git diff -- MANIFEST.sha256
```

Normal validation never updates the manifest.

## Future 0.2.0 release checklist

Do not publish a 0.2.0 archive or release until the hardening pull request is
merged and its CI is green. At release time:

1. verify `VERSION`, `pyproject.toml`, `CHANGELOG.md`, and model revision;
2. run the complete locked validation from a clean signed-off checkout;
3. build the sdist and wheel from the release commit;
4. verify archive contents in a fresh environment;
5. compute SHA-256 values for the exact uploaded assets and current manifest;
6. create an annotated tag with Tarek Zekriti as tagger;
7. publish assets once, then update this table with the immutable tag, commit,
   artifact names, and digests.

No release or tag is created by this remediation branch because its final
metadata and licence decision have not yet been owner-approved.
