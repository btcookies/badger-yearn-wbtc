import brownie
from brownie import SimpleWrapperGatedUpgradeable, interface, accounts, ERC20Upgradeable
import pytest
from badger_utils.token_utils.distribute_from_whales_realtime import (
    distribute_from_whales_realtime_percentage,
)

"""
Test for integration of GAC pausing functionalities to Setts
"""

MAX_UINT256 = 2 ** 256 - 1

LIST_OF_EXPLOITERS = [
    "0xa33B95ea28542Ada32117B60E4F5B4cB7D1Fc19B",
    "0x4fbf7701b3078B5bed6F3e64dF3AE09650eE7DE5",
    "0x1B1b391D1026A4e3fB7F082ede068B25358a61F2",
    "0xEcD91D07b1b6B81d24F2a469de8e47E3fe3050fd",
    "0x691dA2826AC32BBF2a4b5d6f2A07CE07552A9A8E",
    "0x91d65D67FC573605bCb0b5E39F9ef6E18aFA1586",
    "0x0B88A083dc7b8aC2A84eBA02E4acb2e5f2d3063C",
    "0x2eF1b70F195fd0432f9C36fB2eF7C99629B0398c",
    "0xbbfD8041EbDE22A7f3e19600B4bab4925Cc97f7D",
    "0xe06eD65924dB2e7b4c83E07079A424C8a36701E5",
]

BYVWBTC = "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5"
WHALE = "0x6a7ed7a974d4314d2c345bd826daca5501b0aa1e"
TECH_OPS = "0x86cbD0ce0c087b482782c181dA8d191De18C8275"


def test_treasury(proxy_admin, proxy_admin_gov):

    # UPGRADE block
    vault_proxy = SimpleWrapperGatedUpgradeable.at(BYVWBTC)
    governance = accounts.at(vault_proxy.affiliate(), force=True)

    new_vault_logic = SimpleWrapperGatedUpgradeable.deploy({"from": governance})

    prev_affiliate = vault_proxy.affiliate()
    prev_manager = vault_proxy.manager()
    prev_guardian = vault_proxy.guardian()
    prev_wd_fee = vault_proxy.withdrawalFee
    prev_wd_threshold = vault_proxy.withdrawalMaxDeviationThreshold()
    prev_experimental_mode = vault_proxy.experimentalMode()
    prev_experimental_vault = vault_proxy.experimentalVault()

    # Execute upgrade
    proxy_admin.upgrade(vault_proxy, new_vault_logic, {"from": proxy_admin_gov})
    vault_proxy.setTreasury(TECH_OPS, {"from": governance})

    treasury = vault_proxy.treasury()

    assert prev_affiliate == vault_proxy.affiliate()
    assert prev_manager == vault_proxy.manager()
    assert prev_guardian == vault_proxy.guardian()
    assert prev_wd_fee == vault_proxy.withdrawalFee
    assert prev_wd_threshold == vault_proxy.withdrawalMaxDeviationThreshold()
    assert prev_experimental_mode == vault_proxy.experimentalMode()
    assert prev_experimental_vault == vault_proxy.experimentalVault()
    assert TECH_OPS == treasury

    ## You can unpause if GAC is paused or unpaused (SettV1 can't be paused directly)
    if vault_proxy.paused() == True:
        vault_proxy.unpause({"from": governance})

    assert vault_proxy.paused() == False

    ## GAC Pause Block

    ## Get GAC actors
    gac = interface.IGac(vault_proxy.GAC())
    gac_gov = accounts.at(gac.DEV_MULTISIG(), force=True)
    gac_guardian = accounts.at(gac.WAR_ROOM_ACL(), force=True)

    # Focused on testing pausing functionality
    if gac.transferFromDisabled() == True:
        gac.enableTransferFrom({"from": gac_gov})

    # With the vault unpaused and GAC paused test all operations

    # Unpausing globally
    if gac.paused() == True:
        gac.unpause({"from": gac_gov})

    assert gac.paused() == False

    # Transfer funds to user
    user = accounts[3]
    whale = accounts.at(WHALE, force=True)
    whale_balance = int(vault_proxy.balanceOf(WHALE) * 0.8)
    vault_proxy.transfer(user.address, whale_balance, {"from": whale})

    assert vault_proxy.balanceOf(user) > 0

    underlying = ERC20Upgradeable.at(vault_proxy.token())

    # Test wd fee accrued by treasury not governance
    prev_gov_balance = underlying.balanceOf(governance)
    prev_treasury_balance = underlying.balanceOf(treasury)
    vault_proxy.withdraw({"from": user})

    assert underlying.balanceOf(treasury) > prev_treasury_balance
    assert underlying.balanceOf(governance) == prev_gov_balance

    # Testing all operations

    ## Deposit
    prev_shares = vault_proxy.balanceOf(user)
    prev_balance_of_underlying = underlying.balanceOf(user)
    underlying.approve(vault_proxy, MAX_UINT256, {"from": user})
    vault_proxy.deposit(int(underlying.balanceOf(user) / 2), [], {"from": user})
    assert underlying.balanceOf(user) < prev_balance_of_underlying
    assert vault_proxy.balanceOf(user) > prev_shares

    ## Withdraw
    prev_balance_of_underlying = underlying.balanceOf(user)
    amount = int(vault_proxy.balanceOf(user) * 0.6)
    print(vault_proxy.experimentalVault())
    vault_proxy.withdraw(amount, {"from": user})
    assert underlying.balanceOf(user) > prev_balance_of_underlying

    ## DepositAll
    prev_shares = vault_proxy.balanceOf(user)
    prev_balance_of_underlying = underlying.balanceOf(user)
    vault_proxy.deposit([], {"from": user})
    assert underlying.balanceOf(user) < prev_balance_of_underlying
    assert vault_proxy.balanceOf(user) > prev_shares

    ## Transfer From
    rando = accounts[1]
    amount = vault_proxy.balanceOf(user) / 4
    vault_proxy.approve(rando, vault_proxy.balanceOf(user), {"from": user})
    vault_proxy.transferFrom(user.address, rando.address, amount, {"from": rando})
    assert vault_proxy.balanceOf(rando.address) == amount

    # Transfer
    vault_proxy.transfer(accounts[2], amount, {"from": rando})
    assert vault_proxy.balanceOf(accounts[2]) == amount

    ## setTreasury revert
    with brownie.reverts():
        vault_proxy.setTreasury(accounts[4], {"from": rando})

    ## setTreasury success
    prev_treasury = vault_proxy.treasury()
    vault_proxy.setTreasury(WHALE, {"from": governance})
    assert prev_treasury != vault_proxy.treasury()
    assert WHALE == vault_proxy.treasury()
