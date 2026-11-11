# Releasing

## Version numbers

Semantic versioning: `MAJOR.MINOR.PATCH`. While the version starts with `0.`,
a breaking change bumps MINOR.

- **Breaking** — an entity disappears or is renamed, a config entry has to be
  re-created, the minimum Home Assistant version rises.
- **MINOR** — new entities, a new option, support for a new variant.
- **PATCH** — a fix, or a re-vendored library that changes nothing visible.

The version in `custom_components/domeo_evo/manifest.json` is bumped in the
same commit as the change it ships. The release tag is that exact version,
with no `v` prefix: the Marketplace compares the tag with the manifest, and
the release workflow refuses a mismatch.

## Prereleases

A prerelease is `X.Y.Z-beta.N`, published as a GitHub **prerelease**. The
Marketplace offers it only to people who turned on the repository's
Pre-release switch.

Every change that needs a test on a real unit goes through betas:

1. Bump the manifest to `X.Y.Z-beta.1`, merge, and publish `X.Y.Z-beta.1` as a
   prerelease on that commit.
2. A fix during the test bumps to `X.Y.Z-beta.2`, released the same way.
3. Once testers confirm, one commit changes the manifest to `X.Y.Z` and
   nothing else, and `X.Y.Z` is published as a normal release on it.

Never publish a one-digit and a two-digit beta of a version on the same day:
GitHub sorts `-beta.10` before `-beta.9`. Use `X.Y.Z-rc.1` instead, which
sorts after every beta.

## Minimum Home Assistant version

`homeassistant` in `hacs.json` is the oldest release that ships everything the
integration uses (today: `modbus.async_get_unit` and
`async_get_temporary_unit`). Raise it in the release that starts to need a
newer one; that is a breaking change. The Marketplace then keeps offering the
previous release to people on an older Home Assistant.

Tests run against the Home Assistant pinned by
`pytest-homeassistant-custom-component` in `requirements_test.txt`.

## The vendored library

The register map lives in `domeo-evo-modbus` and is copied into
`custom_components/domeo_evo/domeo_evo_modbus/` until it is on PyPI. Change it
there, commit, then run:

```sh
scripts/vendor_domeo_evo_modbus.sh ../domeo-evo-modbus
```

`VENDORED.md` records the commit.

## Publishing

1. Check that the **Tests**, **HACS Action** and **Validate with hassfest**
   workflows pass on `main`.
2. Draft a release with the tag equal to the manifest version. Tick
   **Set as a pre-release** for a beta.
3. Write the notes for the people who run it: what changed for them first,
   any action they must take at the top. GitHub's **Generate release notes**
   gives a starting list (`.github/release.yml` sets the categories).
4. Publish. The **Release** workflow attaches `domeo_evo.zip`, which the
   Marketplace installs.
