## Description

<!-- What does this pull request change, and why? -->

## Related issue

<!-- Every change starts from an issue: "Fixes #123" or "Related to #123". -->

## Testing done

<!-- How did you check it? Tests, the simulator, a real unit (model and variant)? -->

## Checklist

- [ ] `pytest --cov` passes locally (100 % coverage of `custom_components/domeo_modbus`, the vendored library excluded)
- [ ] `ruff check .`, `ruff format --check .` and `mypy` pass locally
- [ ] English and French translations are both updated, if any text changed
- [ ] The manifest version is bumped, if this ships in a release (see `RELEASING.md`)
- [ ] This pull request is about one topic
