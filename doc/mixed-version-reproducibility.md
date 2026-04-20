# Mixed-Version Reproducibility Notes

This note records the provenance and limits of the customized-halving mixed-version interoperability drill.

## Historical baseline

The old-node baseline is the Rincoin v1.0.5 line from the official project history.

Pinned upstream source state:
- Repository: https://github.com/Rin-coin/rincoin
- Branch lineage: master
- Historical boundary used as the baseline: the PR #4 merge into master
- Merge commit recorded by GitHub: b52c87778f800dc5f4e2f59c372badbc139f933f

Important caveat:
- the official repository does not currently publish a downloadable v1.0.5 release asset;
- for that reason, source-building from the pinned historical commit is the preferred reproducible path.

## Preferred reproducible workflow

1. Obtain the historical source corresponding to the pinned master commit above.
2. Build the legacy binaries with the repository release builder:
   - ./contrib/build_release.sh --local
3. Use the linux-ubuntu20 output as the old-node input for the interoperability drill.
4. Point the regression at those binaries:
   - export OLD_RINCOIND=/path/to/legacy/rincoind
   - export OLD_RINCOINCLI=/path/to/legacy/rincoin-cli
5. Run the standardized helper:
   - ./contrib/verify_mixed_version_old_node.sh

## Artifact-based fallback

When a quick source build is not practical, the strongest pinned artifact fallback currently known is:
- Release page: https://github.com/takologi/rincoin/releases/tag/v1.0.5rc1
- Package: https://github.com/takologi/rincoin/releases/download/v1.0.5rc1/rincoin-1.0.5rc1-x86_64-linux-gnu.tar.gz

Observed matching binary fingerprints for the installed legacy drill binaries:
- rincoind: aea74ce203dfd805e45e5a41a42f9d2dac2d8cc96b666c7e817517bce86d346c
- rincoin-cli: f628feb500e5ae0c452453c28e061e58154f614e5ddedb2a71b67ee192711a5a

A system-installed legacy node remains supported only as a convenience fallback.

## What the test proves

The interoperability drill in [test/functional/feature_customized_halving_old_node.py](test/functional/feature_customized_halving_old_node.py) proves:
- coexistence of updated and legacy nodes before activation;
- synchronized progress to the final pre-activation block;
- deterministic divergence when the customized-halving block is mined;
- inability of the legacy node to remain aligned with the activated chain afterward.

## What it does not prove

This drill does not by itself prove:
- complete packaging portability across all Linux runtime environments;
- availability of an official historical binary artifact from the upstream repository;
- every possible network or deployment topology.

## Evidence logs

The standardized helper preserves logs relative to the project root under:
- test-logs/customized_halving_old_node

This is intended for human review and audit evidence retention.

## Test classification

- Default CI-safe checks: the targeted regtest suite in the functional runner.
- Optional extended reproducibility checks: the mixed-version helper driven by pinned old binaries.
- Environment-specific fallback drill: the same helper pointed at a host-local legacy installation.
