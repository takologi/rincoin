
# RinCoin Core

RinCoin is a decentralized digital currency, based on Bitcoin Core, that introduces a new Proof-of-Work hashing algorithm called **RinHash**. RinHash is a hybrid PoW algorithm designed for both security and ASIC-resistance, combining BLAKE3, Argon2d, and SHA3-256. This README provides an overview of RinCoin’s specifications, the RinHash algorithm, and network parameters.

## Mandatory Upgrade Notice

> Rincoin Core 2.0.0-RC1 introduces a consensus-level customized halving change. Nodes running v1.0.5 or earlier will become incompatible with mainnet after block **840000** and will no longer follow the main chain. Operators must upgrade before that height.

## Key Specifications

- **Coin Name / Ticker:** RinCoin (**RIN**)  
- **Consensus Mechanism:** Proof-of-Work (PoW) – **RinHash** algorithm (BLAKE3 → Argon2d → SHA3-256)  
- **Block Target Time:** 1 minute (60 seconds per block)  
- **Block Reward:** 50 RIN (initial coinbase reward per block)  
- **Customized Halving Schedule:** Standard halvings through phase 3, then an explicit fixed schedule beginning at mainnet height 840,000  
- **Difficulty Adjustment:** Every 2016 blocks (~33.6 hours)  
- **Proof-of-Work Hash:** 256-bit output  
- **Address Format:** Base58 addresses start with **R**  
- **Network Ports:** P2P: 9555, RPC: 9556  
- **Network Magic:** 0x52 0x49 0x4E 0x43 ("RINC")  

## Proof-of-Work Algorithm: RinHash

RinHash is a custom proof-of-work algorithm using:

1. **BLAKE3**: Fast initial hashing  
2. **Argon2d**: Memory-hard step to resist ASICs  
3. **SHA3-256**: Final standard cryptographic hash

A valid block satisfies:  
`SHA3-256( Argon2d( BLAKE3(block_header) )) < Target`

This design provides:
- Fast verification
- Memory-hardness to deter ASICs
- Compatibility with existing 256-bit PoW frameworks

## Customized Halving Activation

This project uses a consensus-critical customized post-phase-3 subsidy schedule. The upgrade line for this change is Rincoin Core 2.0.0 with protocol version 70018, and the current workspace metadata is staged as a 2.0.0 release-candidate build.

### Activation heights

- Mainnet: 840000
- Testnet: 4200
- Regtest: 600

Public testnet now uses a 200x compressed rehearsal schedule, with a 1050-block halving interval instead of the 210000-block mainnet interval. This keeps the subsidy logic aligned while making activation reachable in practical time.

### Customized halving overview

The inherited halving schedule remains unchanged through phase 3. Starting at the activation height for each network, the post-phase-3 subsidy follows an explicit Rincoin schedule instead of continuing the inherited standard-halving progression. This is a consensus-level rule change.

Mainnet subsidy schedule:
- Heights 0 to 209,999: 50 RIN
- Heights 210,000 to 419,999: 25 RIN
- Heights 420,000 to 629,999: 12.5 RIN
- Heights 630,000 to 839,999: 6.25 RIN
- Heights 840,000 to 2,099,999: 4 RIN
- Heights 2,100,000 to 4,199,999: 2 RIN
- Heights 4,200,000 to 6,299,999: 1 RIN
- Heights 6,300,000 and above: 0.6 RIN

The phase-4 reward of 4 RIN is intentional and replaces the natural 3.125 RIN standard-halving outcome. Testnet and regtest use lower activation heights so the transition can be rehearsed in non-mainnet environments. The current public testnet profile is deliberately accelerated, with halvings every 1050 blocks and the customized phase-4 activation at height 4200. Nodes running v1.0.5 or earlier will become incompatible after mainnet height 840000 and must be upgraded before that point. Legacy peers may still connect before activation, but are treated as obsolete once the customized schedule is active.

The repository now includes both regtest consensus coverage and a real mixed-version old-node drill against the pinned v1.0.5 baseline line, including separate RPC and P2P port assignments for the old and new nodes. The preferred reproducibility path is to build the historical baseline from the pinned master commit and run the preserved-log helper in [contrib/verify_mixed_version_old_node.sh](contrib/verify_mixed_version_old_node.sh).

Developer notes for the consensus boundary, peer-version handling, mixed-version provenance, and verification workflow are summarized in [doc/customized-halving.md](doc/customized-halving.md) and [doc/mixed-version-reproducibility.md](doc/mixed-version-reproducibility.md).

## Network and Usage

- **Magic bytes:** `0x52 0x49 0x4E 0x43`  
- **Ports:** 9555 (P2P), 9556 (RPC)  
- **Mining:** CPU/GPU mining supported  
- **Wallet:** Full-node wallet with RIN units

## Building Rincoin

For detailed instructions on building release binaries for Linux and Windows, see [doc/build-rincoin-release.md](doc/build-rincoin-release.md).

Quick start for building from source:
- [Linux/Unix Build Notes](doc/build-unix.md)
- [Windows Build Notes](doc/build-windows.md)
- [Release Build Guide](doc/build-rincoin-release.md)

## Developer Notes

See `chainparams.cpp` for network configuration.  
See `GetPoWHash()` for RinHash implementation.  

## Rincoin Communitys
[![Discord Banner 2](https://discord.com/api/guilds/1354664874176680017/widget.png?style=banner2)](https://discord.gg/Ap7TUXYRBf)