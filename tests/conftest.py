from brownie import (
    accounts,
    interface,
    Controller,
    SettV4,
)
from config import (
    BADGER_DEV_MULTISIG,
    WANT,
    LP_COMPONENT,
    REWARD_TOKEN,
    PROTECTED_TOKENS,
    FEES,
)
from dotmap import DotMap
import pytest

@pytest.fixture
def proxy_admin():
    """
     Verify by doing web3.eth.getStorageAt("STRAT_ADDRESS", int(
        0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103
    )).hex()
    """
    return interface.IProxyAdmin("0x20dce41acca85e8222d6861aa6d23b6c941777bf")


@pytest.fixture
def proxy_admin_gov():
    """
        Also found at proxy_admin.owner()
    """
    return accounts.at("0x21cf9b77f88adf8f8c98d7e33fe601dc57bc0893", force=True)


## Contracts ##


@pytest.fixture
def vault(deployed):
    return deployed.vault


@pytest.fixture
def sett(deployed):
    return deployed.sett


@pytest.fixture
def controller(deployed):
    return deployed.controller


@pytest.fixture
def strategy(deployed):
    return deployed.strategy


## Tokens ##


@pytest.fixture
def want(deployed):
    return deployed.want


@pytest.fixture
def tokens():
    return [WANT, LP_COMPONENT, REWARD_TOKEN]


## Accounts ##


@pytest.fixture
def deployer(deployed):
    return deployed.deployer


@pytest.fixture
def strategist(strategy):
    return accounts.at(strategy.strategist(), force=True)


@pytest.fixture
def settKeeper(vault):
    return accounts.at(vault.keeper(), force=True)


@pytest.fixture
def strategyKeeper(strategy):
    return accounts.at(strategy.keeper(), force=True)

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
