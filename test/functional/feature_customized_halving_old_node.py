#!/usr/bin/env python3
# Copyright (c) 2026
# Distributed under the MIT software license.
"""Mixed-version regression for the customized halving activation.

This test runs a new node from the current workspace against a pinned legacy
Rincoin v1.0.5 baseline binary. The legacy binary path can be provided through
OLD_RINCOIND and OLD_RINCOINCLI for reproducible source-built or artifact-based
verification; a system-installed binary is only the fallback. It verifies that:

1. old and new nodes can coexist and sync before activation;
2. the old node is still treated as legacy-but-valid before activation;
3. the new node activates the customized subsidy at the expected height;
4. the old node does not follow the post-activation chain;
5. the connection is dropped once the old node becomes obsolete.
"""

import os

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, p2p_port, rpc_port

OLD_RINCOIND = os.environ.get("OLD_RINCOIND", "/usr/local/bin/rincoind")
OLD_RINCOINCLI = os.environ.get("OLD_RINCOINCLI", "/usr/local/bin/rincoin-cli")


class CustomizedHalvingOldNodeTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.supports_cli = False
        disable_mweb = "-vbparams=mweb:4102444800:4102444801"
        self.extra_args = [
            [disable_mweb, "-uacomment=newhalving"],
            [disable_mweb, "-uacomment=old105"],
        ]

    def setup_nodes(self):
        assert os.path.isfile(OLD_RINCOIND)
        assert os.path.isfile(OLD_RINCOINCLI)
        assert p2p_port(0) != p2p_port(1)
        assert rpc_port(0) != rpc_port(1)

        self.add_nodes(
            self.num_nodes,
            extra_args=self.extra_args,
            binary=[self.options.bitcoind, OLD_RINCOIND],
            binary_cli=[self.options.bitcoincli, OLD_RINCOINCLI],
        )
        self.start_nodes()
        self.import_deterministic_coinbase_privkeys()

    def run_test(self):
        new_node, old_node = self.nodes

        self.log.info("Confirm version split and distinct port assignments")
        new_info = new_node.getnetworkinfo()
        old_info = old_node.getnetworkinfo()
        assert_equal(new_info["protocolversion"], 70018)
        assert_equal(old_info["protocolversion"], 70017)

        self.log.info("Verify mixed-version peers coexist before activation")
        self.connect_nodes(1, 0)
        self.sync_all()
        peer = next(peer for peer in new_node.getpeerinfo() if peer["version"] == 70017)
        assert_equal(peer["customized_halving_ready"], False)
        assert_equal(peer["customized_halving_obsolete"], False)

        self.log.info("Mine to the last pre-activation height and confirm sync")
        new_node.generatetoaddress(599, new_node.get_deterministic_priv_key().address)
        self.sync_blocks()
        assert_equal(new_node.getblockchaininfo()["blocks"], 599)
        assert_equal(old_node.getblockchaininfo()["blocks"], 599)
        assert any(peer["version"] == 70017 for peer in new_node.getpeerinfo())

        self.log.info("Activate the customized halving on the new node")
        new_node.generatetoaddress(1, new_node.get_deterministic_priv_key().address)
        assert_equal(new_node.getblockchaininfo()["blocks"], 600)
        assert_equal(new_node.getblockchaininfo()["customized_halving"]["active"], True)

        self.log.info("Old node must not follow the activated chain")
        self.wait_until(lambda: old_node.getblockchaininfo()["blocks"] == 599)
        self.wait_until(lambda: len(new_node.getpeerinfo()) == 0, timeout=30)

        self.log.info("Reconnection attempt from the old node should not persist")
        old_node.addnode("127.0.0.1:{}".format(p2p_port(0)), "onetry")
        self.wait_until(lambda: len(new_node.getpeerinfo()) == 0, timeout=30)


if __name__ == '__main__':
    CustomizedHalvingOldNodeTest().main()
