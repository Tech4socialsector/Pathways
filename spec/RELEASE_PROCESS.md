# Release Process

How to prepare, tag and publish a Pathways release.

## Branches and versions

- `TFSS` is the default branch. Releases are tagged on it.
- Tags are `vMAJOR.MINOR.PATCH` (for example `v0.4.0`), following [Semantic Versioning](https://semver.org/):

| Change in the release | Bump | Example |
|---|---|---|
| Breaking change: DocType or field renamed or removed, API contract changed, admin action required | MAJOR | 1.4.2 → 2.0.0 |
| New backward-compatible feature | MINOR | 1.4.2 → 1.5.0 |
| Backward-compatible bug fixes only | PATCH | 1.4.2 → 1.4.3 |

- Below 1.0.0, breaking changes bump MINOR (0.3.0 → 0.4.0) and are listed under **Breaking changes**.
- Release 1.0.0 when Pathways goes into production use. After that, follow the table above strictly.

## 1. Prepare the release

1. Make sure `TFSS` is up to date and the working tree is clean:
   ```bash
   git checkout TFSS && git pull
   git status
   ```
2. Check `pathways/patches.txt` for leftover merge-conflict markers, and check that every patch listed there exists.
3. Run the tests on a test site:
   ```bash
   bench --site <test-site> run-tests --app pathways
   ```
4. Build the frontend to confirm it compiles: `bench build --app pathways`.

## 2. Review the Git history

```bash
git describe --tags --abbrev=0                      # previous release tag
git log --oneline <previous-tag>..TFSS              # commits in this release
git diff --stat <previous-tag>..TFSS -- . ':!pathways/public'
git diff <previous-tag>..TFSS -- pathways/patches.txt
git diff --name-status <previous-tag>..TFSS -- 'pathways/pathways/doctype/*/*.json'
```

For each commit, read the diff, not only the message. Record:

- new or removed DocTypes, fields and options;
- new, changed or removed whitelisted APIs;
- permission changes in DocType JSON and in `pathways/api/access.py`;
- new patches in `patches.txt` and what they change;
- changes to `hooks.py` (scheduler, page renderers, session hooks);
- dependency changes in `pyproject.toml` and `frontend/package.json`.

If a later commit replaces an earlier one in the same release, document only the final behaviour.

## 3. Select the version number

Use the table above. Any item under Breaking changes means a MAJOR bump (MINOR below 1.0.0).

## 4. Prepare the release notes

1. Copy [releases/TEMPLATE.md](releases/TEMPLATE.md) to `spec/releases/vX.Y.Z.md` and fill it in.
2. Add a new section at the top of [CHANGELOG.md](../CHANGELOG.md) (under `[Unreleased]`) and update the compare links at the bottom.
3. Replace [RELEASE_NOTES.md](../RELEASE_NOTES.md) with the stakeholder summary for the new release.
4. Set `__version__` in `pathways/__init__.py` to the new version.
5. Open a pull request titled `docs(release): vX.Y.Z` and get it reviewed.

Rules for every document:
- Check each item against the code.
- List each change once, in the most fitting section.
- Leave out personal data, credentials, internal hostnames and reviewers' names.

## 5. Test the release

On a staging site restored from a recent production backup:

```bash
cd apps/pathways && git checkout TFSS && git pull && cd ../..
bench --site <staging-site> migrate
bench build --app pathways
bench restart
```

Then:
- Confirm `migrate` finished without errors and every new patch ran (`tabPatch Log`).
- Follow the affected sections of the [Testing Guide](TESTING_GUIDE.md).
- Check each item under Upgrade considerations in the release document.

## 6. Create the Git tag

After the release pull request is merged:

```bash
git checkout TFSS && git pull
git tag -a vX.Y.Z -m "Pathways vX.Y.Z"
git push origin vX.Y.Z
```

## 7. Publish the GitHub Release

1. On GitHub, go to **Releases › Draft a new release** and choose the tag `vX.Y.Z`.
2. Title: `Pathways vX.Y.Z`.
3. Paste the contents of `spec/releases/vX.Y.Z.md` as the description. **Generate release notes** can add the list of merged pull requests, grouped by `.github/release.yml`.
4. Tick **Set as a pre-release** for versions below 1.0.0, if the team prefers.
5. Publish.

## 8. Maintain the changelog

- Add entries to `[Unreleased]` in `CHANGELOG.md` as pull requests are merged. This makes the release step quicker.
- Keep releases in reverse chronological order.
- Use the sections Added, Changed, Fixed, Security, Technical, Breaking Changes and Migration Notes, and leave out empty ones.
- Never edit a published release's entry, except to correct a factual error.

## Pull request labels

`.github/release.yml` groups generated release notes by label:

| Label | Section |
|---|---|
| `breaking-change` | Breaking Changes |
| `enhancement` | New Features |
| `bug` | Bug Fixes |
| `security` | Security |
| `documentation` | Documentation |
| `skip-changelog` | Not listed |

Pull request titles must follow Conventional Commits (`feat`, `fix`, `docs`, `ci`, and so on). The `PR Title` workflow checks this.
