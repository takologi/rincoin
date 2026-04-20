// Copyright (c) 2014-2019 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <net.h>
#include <signet.h>
#include <validation.h>

#include <test/util/setup_common.h>

#include <boost/test/unit_test.hpp>

BOOST_FIXTURE_TEST_SUITE(validation_tests, TestingSetup)

static CAmount ExpectedCustomizedSubsidy(int nHeight, const Consensus::Params& consensusParams)
{
    if (consensusParams.HasCustomizedHalvingSchedule()) {
        if (nHeight >= consensusParams.nCustomizedHalvingTailStartHeight) return consensusParams.nCustomizedHalvingTailSubsidy;
        if (nHeight >= consensusParams.nCustomizedHalvingPhase6StartHeight) return consensusParams.nCustomizedHalvingPhase6Subsidy;
        if (nHeight >= consensusParams.nCustomizedHalvingPhase5StartHeight) return consensusParams.nCustomizedHalvingPhase5Subsidy;
        if (nHeight >= consensusParams.nCustomizedHalvingPhase4StartHeight) return consensusParams.nCustomizedHalvingPhase4Subsidy;
    }

    int halvings = nHeight / consensusParams.nSubsidyHalvingInterval;
    if (halvings >= 64) return 0;

    CAmount subsidy = 50 * COIN;
    subsidy >>= halvings;
    return subsidy;
}

BOOST_AUTO_TEST_CASE(block_subsidy_test)
{
    const auto main_chain_params = CreateChainParams(*m_node.args, CBaseChainParams::MAIN);
    const auto test_chain_params = CreateChainParams(*m_node.args, CBaseChainParams::TESTNET);
    const auto regtest_chain_params = CreateChainParams(*m_node.args, CBaseChainParams::REGTEST);

    const Consensus::Params& main_params = main_chain_params->GetConsensus();
    const Consensus::Params& test_params = test_chain_params->GetConsensus();
    const Consensus::Params& regtest_params = regtest_chain_params->GetConsensus();

    BOOST_REQUIRE(main_params.HasCustomizedHalvingSchedule());
    BOOST_REQUIRE(test_params.HasCustomizedHalvingSchedule());
    BOOST_REQUIRE(regtest_params.HasCustomizedHalvingSchedule());

    BOOST_CHECK_EQUAL(main_params.nCustomizedHalvingPhase4StartHeight, 840000);
    BOOST_CHECK_EQUAL(main_params.nCustomizedHalvingPhase5StartHeight, 2100000);
    BOOST_CHECK_EQUAL(main_params.nCustomizedHalvingPhase6StartHeight, 4200000);
    BOOST_CHECK_EQUAL(main_params.nCustomizedHalvingTailStartHeight, 6300000);

    BOOST_CHECK_EQUAL(test_params.nCustomizedHalvingPhase4StartHeight, 50000);
    BOOST_CHECK_EQUAL(test_params.nCustomizedHalvingPhase5StartHeight, 125000);
    BOOST_CHECK_EQUAL(test_params.nCustomizedHalvingPhase6StartHeight, 250000);
    BOOST_CHECK_EQUAL(test_params.nCustomizedHalvingTailStartHeight, 375000);

    BOOST_CHECK_EQUAL(regtest_params.nCustomizedHalvingPhase4StartHeight, 600);
    BOOST_CHECK_EQUAL(regtest_params.nCustomizedHalvingPhase5StartHeight, 1500);
    BOOST_CHECK_EQUAL(regtest_params.nCustomizedHalvingPhase6StartHeight, 3000);
    BOOST_CHECK_EQUAL(regtest_params.nCustomizedHalvingTailStartHeight, 4500);

    const std::vector<int> main_boundary_heights{
        0,
        1,
        209998, 209999, 210000, 210001,
        419998, 419999, 420000, 420001,
        629998, 629999, 630000, 630001,
        839998, 839999, 840000, 840001,
        2099998, 2099999, 2100000, 2100001,
        4199998, 4199999, 4200000, 4200001,
        6299998, 6299999, 6300000, 6300001,
        10000000,
    };

    for (int height : main_boundary_heights) {
        BOOST_CHECK_EQUAL(GetBlockSubsidy(height, main_params), ExpectedCustomizedSubsidy(height, main_params));
    }

    const std::vector<int> testnet_boundary_heights{
        0,
        49999, 50000, 50001,
        124999, 125000, 125001,
        249999, 250000, 250001,
        374999, 375000, 375001,
    };

    for (int height : testnet_boundary_heights) {
        BOOST_CHECK_EQUAL(GetBlockSubsidy(height, test_params), ExpectedCustomizedSubsidy(height, test_params));
    }

    const std::vector<int> regtest_boundary_heights{
        0,
        149, 150, 151,
        299, 300, 301,
        449, 450, 451,
        599, 600, 601,
        1499, 1500, 1501,
        2999, 3000, 3001,
        4499, 4500, 4501,
    };

    for (int height : regtest_boundary_heights) {
        BOOST_CHECK_EQUAL(GetBlockSubsidy(height, regtest_params), ExpectedCustomizedSubsidy(height, regtest_params));
    }
}

BOOST_AUTO_TEST_CASE(subsidy_limit_test)
{
    const auto chainParams = CreateChainParams(*m_node.args, CBaseChainParams::MAIN);
    CAmount nSum = 0;
    for (int nHeight = 0; nHeight < 56000000; nHeight += 1000) {
        CAmount nSubsidy = GetBlockSubsidy(nHeight, chainParams->GetConsensus());
        BOOST_CHECK(nSubsidy <= 50 * COIN);
        nSum += nSubsidy * 1000;
        BOOST_CHECK(MoneyRange(nSum));
    }
    BOOST_CHECK_EQUAL(nSum, CAmount{6084750000000000});
}

BOOST_AUTO_TEST_SUITE_END()
