<!--
Copy to spec/releases/vX.Y.Z.md and fill in. Delete any section that has nothing in it,
except Breaking changes (write "None.").
Every item must be checked against the code and the Git history, not taken from commit
messages alone. Write for the reader: what changed, for whom, and what they must do.
Do not include personal data, credentials, internal hostnames or reviewers' names.
-->

# Pathways vX.Y.Z

**Release date:** YYYY-MM-DD
**Commit range:** [vA.B.C...vX.Y.Z](https://github.com/Tech4socialsector/Pathways/compare/vA.B.C...vX.Y.Z) (first..last short SHA)
**Type:** Major | Minor | Patch

## Summary

Two or three sentences in plain language: what this release does and who it helps.

## Feature highlights

- The three to five changes users will notice most.

## Module-wise changes

### <Module name>
- **Introduced:** new capability.
- **Modified:** changed behaviour.
- **Removed:** anything taken away.
- **Fixed:** defects resolved in this module.
- **Problem addressed:** why the change was made.
- **Roles affected:** Pathways roles, candidates, or none.
- **Administrator action:** what to do after upgrading, or "none".

## Bug fixes

- What users saw before, stated as fixed.

## Security enhancements

- Permission, privacy or data-exposure changes.

## Technical changes

- DocTypes and fields added, changed or removed.
- APIs added, changed or removed.
- Hooks, scheduler jobs, dependencies, build changes.

## Breaking changes

| Change | Who is affected | Action |
|---|---|---|
| | | |

## Deployment instructions

```bash
cd <bench>
bench --site <site> backup --with-files
cd apps/pathways && git fetch && git checkout vX.Y.Z && cd ../..
bench --site <site> migrate
bench build --app pathways
bench restart
```

### Patches run by `migrate`

| Patch | Effect |
|---|---|
| `pathways.patches.v1_0.<name>` | |

## Upgrade considerations

- Data to check before upgrading, settings to review afterwards.
