#!/usr/bin/env python3
# Copyright (c) 2026
# Distributed under the MIT software license.
"""Purpose-built regression coverage for the customized halving boundary.

This test verifies the highest-risk activation behaviors directly:
1. fee-aware coinbase maximum enforcement around the height-600 activation;
2. underpay remains valid even when fees are present;
3. old-rule overpay is rejected after activation;
4. peer obsolescence follows the active chain tip and toggles correctly after a rewind.
"""

from test_framework.blocktools import create_block, create_coinbase, create_tx_with_script
from test_framework.messages import COIN, msg_version
from test_framework.p2p import P2PDataStore, P2PInterface
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class CustomizedHalvingBoundaryTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.supports_cli = False
        self.extra_args = [["-whitelist=noban@127.0.0.1", "-vbparams=mweb:4102444800:4102444801"]]

    def run_test(self):
        node = self.nodes[0]
        peer = node.add_p2p_connection(P2PDataStore())

        self.log.info("Create spendable anyone-can-spend coinbases for fee-aware boundary blocks")
        best_block = node.getblock(node.getbestblockhash())
        tip = int(node.getbestblockhash(), 16)
        block_time = best_block["time"] + 1
        spendable_coinbases = []

        for height in range(1, 5):
            block = create_block(tip, create_coinbase(height), block_time, version=0x20000000)
            block.solve()
            peer.send_blocks_and_test([block], node, success=True)
            spendable_coinbases.append(block.vtx[0])
            tip = block.sha256
            block_time += 1

        # Mature the handmade coinbases and stop one block before the activation rehearsal range.
        node.generatetoaddress(594, node.get_deterministic_priv_key().address)
        assert_equal(node.getblockchaininfo()["blocks"], 598)

        best_block = node.getblock(node.getbestblockhash())
        tip = int(node.getbestblockhash(), 16)
        block_time = best_block["time"] + 1

        self.log.info("Underpay with fees present is valid before activation because the cap is still legacy")
        fee_a = 1_000_000
        spend_a = create_tx_with_script(spendable_coinbases[0], 0, script_sig=b'\x51', amount=50 * COIN - fee_a)
        pre_activation = create_block(tip, create_coinbase(599, fees=fee_a), block_time, version=0x20000000, txlist=[spend_a])
        pre_activation.vtx[0].vout[0].nValue = 4 * COIN + fee_a
        pre_activation.vtx[0].rehash()
        pre_activation.hashMerkleRoot = pre_activation.calc_merkle_root()
        pre_activation.rehash()
        pre_activation.solve()
        peer.send_blocks_and_test([pre_activation], node, success=True)

        self.log.info("Exact subsidy-plus-fees limit is valid at the activation height")
        fee_b = 2_000_000
        spend_b = create_tx_with_script(spendable_coinbases[1], 0, script_sig=b'\x51', amount=50 * COIN - fee_b)
        activation = create_block(pre_activation.sha256, create_coinbase(600, fees=fee_b), block_time + 1, version=0x20000000, txlist=[spend_b])
        activation.solve()
        peer.send_blocks_and_test([activation], node, success=True)
        assert_equal(node.getblockchaininfo()["blocks"], 600)
        assert_equal(node.getblockchaininfo()["customized_halving"]["active"], True)

        self.log.info("Old-rule 6.25 RIN reward plus fees must be rejected after activation")
        fee_c = 3_000_000
        spend_c = create_tx_with_script(spendable_coinbases[2], 0, script_sig=b'\x51', amount=50 * COIN - fee_c)
        old_rule_overpay = create_block(activation.sha256, create_coinbase(601, fees=fee_c), block_time + 2, version=0x20000000, txlist=[spend_c])
        old_rule_overpay.vtx[0].vout[0].nValue = 625000000 + fee_c
        old_rule_overpay.vtx[0].rehash()
        old_rule_overpay.hashMerkleRoot = old_rule_overpay.calc_merkle_root()
        old_rule_overpay.rehash()
        old_rule_overpay.solve()
        peer.send_blocks_and_test([old_rule_overpay], node, success=False, reject_reason='bad-cb-amount')

        self.log.info("Even a one-satoshi overpay above subsidy plus fees must be rejected")
        fee_d = 4_000_000
        spend_d = create_tx_with_script(spendable_coinbases[3], 0, script_sig=b'\x51', amount=50 * COIN - fee_d)
        one_sat_high = create_block(activation.sha256, create_coinbase(601, fees=fee_d), block_time + 3, version=0x20000000, txlist=[spend_d])
        one_sat_high.vtx[0].vout[0].nValue = 4 * COIN + fee_d + 1
        one_sat_high.vtx[0].rehash()
        one_sat_high.hashMerkleRoot = one_sat_high.calc_merkle_root()
        one_sat_high.rehash()
        one_sat_high.solve()
        peer.send_blocks_and_test([one_sat_high], node, success=False, reject_reason='bad-cb-amount')

        self.log.info("Legacy peers are obsolete on the active post-activation chain")
        legacy_after_activation = node.add_p2p_connection(P2PInterface(), send_version=False, wait_for_verack=False)
        legacy_after_activation_msg = msg_version()
        legacy_after_activation_msg.nVersion = 70017
        with node.assert_debug_log(['version 70017 is obsolete after customized halving activation']):
            legacy_after_activation.send_message(legacy_after_activation_msg)
            legacy_after_activation.wait_for_disconnect()

        self.log.info("Rewind below the boundary and confirm legacy peer acceptance returns")
        activation_hash = node.getblockhash(600)
        node.invalidateblock(activation_hash)
        assert_equal(node.getblockchaininfo()["blocks"], 599)
        assert_equal(node.getblockchaininfo()["customized_halving"]["active"], False)

        legacy_after_rewind = node.add_p2p_connection(P2PInterface(), send_version=False, wait_for_verack=False)
        legacy_after_rewind_msg = msg_version()
        legacy_after_rewind_msg.nVersion = 70017
        legacy_after_rewind.send_message(legacy_after_rewind_msg)
        legacy_after_rewind.wait_for_verack()
        assert legacy_after_rewind.is_connected
        legacy_peer_info = next(peerinfo for peerinfo in node.getpeerinfo() if peerinfo['version'] == 70017)
        assert_equal(legacy_peer_info['customized_halving_ready'], False)
        assert_equal(legacy_peer_info['customized_halving_obsolete'], False)

        self.log.info("Re-activate the boundary block and verify the connected legacy peer is dropped again")
        with node.assert_debug_log(['became obsolete after customized halving activation']):
            node.reconsiderblock(activation_hash)
            self.wait_until(lambda: node.getblockchaininfo()["blocks"] == 600)
            legacy_after_rewind.wait_for_disconnect()


if __name__ == '__main__':
    CustomizedHalvingBoundaryTest().main()
