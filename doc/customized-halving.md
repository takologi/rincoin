# Customized Halving Developer Notes

This repository implements a consensus-changing customized subsidy schedule. The change is consensus-critical and requires a coordinated operator upgrade.

## Operator upgrade notice

- Mainnet activation height: 840000
- Testnet activation height: 4200
- Regtest activation height: 600

Public testnet uses an accelerated rehearsal profile with a 1050-block halving interval, which is 200x faster than the mainnet interval of 210000 blocks.

Nodes running v1.0.5 or earlier will not remain compatible after mainnet height 840000. Upgrade to the v2.0.0 line before that boundary.

## Consensus rule

The consensus-critical subsidy logic lives in:
- [src/validation.cpp](src/validation.cpp)
- [src/consensus/params.h](src/consensus/params.h)
- [src/chainparams.cpp](src/chainparams.cpp)

The network switches by block height, not by timestamp.

### Activation and later schedule boundaries

The first activation height for each network is:
- Mainnet: 840000
- Testnet: 4200
- Regtest: 600

Later post-activation schedule boundaries are:
- Mainnet: 2100000, 4200000, 6300000
- Testnet: 10500, 21000, 31500
- Regtest: 1500, 3000, 4500

### Subsidy schedule

- 50 RIN
- 25 RIN
- 12.5 RIN
- 6.25 RIN
- 4 RIN
- 2 RIN
- 1 RIN
- 0.6 RIN tail

The phase-4 reward of 4 RIN is intentional and consensus-critical.

## Peer-version handling

Protocol version 70018 is the customized-halving readiness marker. The workspace build metadata is currently staged as a 2.0.0 release-candidate build.

- Before activation, peers below 70018 are still accepted if they are otherwise valid.
- After activation, peers below 70018 are considered obsolete and are disconnected in the networking path.
- This peer gate is only a coordination aid. Block validation remains the actual consensus enforcement mechanism.

Relevant files:
- [src/version.h](src/version.h)
- [src/net_processing.cpp](src/net_processing.cpp)
- [src/rpc/net.cpp](src/rpc/net.cpp)

## RPC diagnostics

Readiness and post-activation state are exposed through:
- [src/rpc/blockchain.cpp](src/rpc/blockchain.cpp)
- [src/rpc/mining.cpp](src/rpc/mining.cpp)

Key RPCs:
- getblockchaininfo
- getblocktemplate
- getpeerinfo

## Regtest rehearsal

Regtest activates at height 600 so the full transition can be exercised quickly in automated tests.

## Verification commands

Use the project virtual environment for the Python functional tests.

- Native consensus and miner checks:
  ./src/test/test_litecoin --run_test=validation_tests,mining_tests

- Default CI-safe functional consensus and peer-policy checks:
  . .venv/bin/activate && python3 test/functional/test_runner.py mining_basic.py feature_customized_halving_boundary.py rpc_blockchain.py p2p_invalid_block.py p2p_leak.py

- The purpose-built boundary regression in [test/functional/feature_customized_halving_boundary.py](test/functional/feature_customized_halving_boundary.py) covers fee-aware coinbase limits, underpay-vs-overpay semantics, and active-tip rewind behavior for obsolete peers.

## Mixed-version reproducibility and provenance

The historical baseline for the interoperability drill is the v1.0.5 line from the official Rincoin master history, specifically the PR #4 merge on the upstream master branch. The merged master commit recorded by GitHub is:
- b52c87778f800dc5f4e2f59c372badbc139f933f

Because the official repository does not currently publish a downloadable v1.0.5 release asset, the strongest reproducible path is:
1. obtain the old source from that pinned historical master state;
2. build it with [contrib/build_release.sh](contrib/build_release.sh) for the linux-ubuntu20 target;
3. point the interoperability test at the resulting legacy binaries using OLD_RINCOIND and OLD_RINCOINCLI.

A practical fallback is to use the checksum-verified v1.0.5rc1 Linux artifact published at the release URL provided by the maintainer. A host-local system installation is supported only as the final fallback.

- Standardized extended verification with preserved logs relative to the project root:
  OLD_RINCOIND=/path/to/old/rincoind OLD_RINCOINCLI=/path/to/old/rincoin-cli ./contrib/verify_mixed_version_old_node.sh

- The helper preserves evidence under:
  test-logs/customized_halving_old_node

What this drill proves:
- coexistence before activation;
- synchronized progress to the last pre-activation block;
- divergence at the activation boundary;
- inability of the obsolete legacy node to remain aligned afterward.

What it does not prove:
- broad cross-platform packaging portability;
- CI-level artifact availability from the official repository;
- every possible network-environment variation.

The mixed-version drill uses separate RPC and P2P ports automatically and is intended as an optional extended reproducibility test rather than a default CI-safe check.

For the exact historical provenance, artifact fallback, and evidence-log conventions, see [doc/mixed-version-reproducibility.md](doc/mixed-version-reproducibility.md).

## Intentional upstream naming that remains

Some framework names such as BitcoinTestFramework remain because they refer to inherited upstream test infrastructure, not to Rincoin network identity or consensus parameters.
