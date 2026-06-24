#!/usr/bin/env python3
"""
Stabilizer Finance — Auto BOT
Automated volume farming on Stabilizer Finance testnet for efficient SP point accumulation.

Author: hourx
GitHub: https://github.com/hourx
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

import pytz
from colorama import Fore, Style, init
from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

# Initialize colorama and load .env
init(autoreset=True)
load_dotenv()

# Timezone
wib = pytz.timezone("Asia/Jakarta")


class StabilizerFinance:
    def __init__(self):
        # Config from .env
        self.SWAP_AMOUNT = int(os.getenv("SWAP_AMOUNT", 50000))
        self.DAILY_CAP = int(os.getenv("DAILY_CAP", 20000))
        self.RPC_URL = os.getenv("RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")

        # Contract addresses
        self.ROUTER = "0xFa6419a3d3503a016dF3A59F690734862CA2A78D"
        self.AMM = "0xA3E36262f6899e27bB4B1802e8298e843E74CBC7"

        # Token addresses
        self.TOKENS = {
            "USDT": "0xee0418Bd560613fbcF924C36235AB1ec301D4933",
            "USDC": "0x77ef087024F87976aAdA0Aa7F73BB8EAe6E9dda1",
            "USDS": "0xF85938e2Bfc178026f60c5Ea50cC347D42C73b3D",
            "PYUSD": "0xF11Cf5a42c0a4F7e5BADe92c634Fd2649F4Ef53e",
            "USDZ": "0x55Cc481D28Db3f1ffc9347745AA6fbB940505BdD",
        }

        # Explorer
        self.EXPLORER = "https://sepolia.etherscan.io/tx/"

        # API base
        self.API_BASE = "https://app.stabilizer.finance"

        # Decimal
        self.DECIMALS = 18

        # ABIs
        self.ERC20_ABI = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        ]

        self.ROUTER_ABI = [
            {
                "inputs": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "minAmountOut", "type": "uint256"}
                ],
                "name": "swap",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"}
                ],
                "name": "getAmountOut",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        # Accounts and proxies
        self.ACCOUNTS = []
        self.PROXIES = []
        self.ACCOUNT_PROXIES = {}
        self.W3 = None

    def welcome(self):
        print(
            f"""
    {Fore.GREEN + Style.BRIGHT}╔══════════════════════════════════════╗{Style.RESET_ALL}
    {Fore.GREEN + Style.BRIGHT}║{Style.RESET_ALL}  {Fore.GREEN + Style.BRIGHT}Siba{Style.RESET_ALL} {Fore.BLUE + Style.BRIGHT}Agent{Style.RESET_ALL}                          {Fore.GREEN + Style.BRIGHT}║{Style.RESET_ALL}
    {Fore.GREEN + Style.BRIGHT}║{Style.RESET_ALL}  {Fore.WHITE + Style.BRIGHT}Stabilizer Finance {Fore.BLUE + Style.BRIGHT}Auto BOT{Style.RESET_ALL}        {Fore.GREEN + Style.BRIGHT}║{Style.RESET_ALL}
    {Fore.GREEN + Style.BRIGHT}╚══════════════════════════════════════╝{Style.RESET_ALL}

    {Fore.YELLOW + Style.BRIGHT}⚡ github.com/hourx{Style.RESET_ALL}
        """
        )

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def print_question(self, prompt):
        return input(
            f"{Fore.CYAN + Style.BRIGHT}[ ? ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {prompt} : {Style.RESET_ALL}"
        )

    def load_accounts(self):
        accounts_file = "accounts.txt"
        try:
            if not os.path.exists(accounts_file):
                self.log(f"Accounts : {Fore.YELLOW}File not found, creating...{Style.RESET_ALL}")
                with open(accounts_file, "w") as f:
                    f.write("# One private key per line\n")
                return []

            with open(accounts_file, "r") as f:
                lines = f.readlines()

            accounts = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        addr = Account.from_key(line).address
                        accounts.append({"private_key": line, "address": addr})
                    except Exception as e:
                        self.log(f"Accounts : {Fore.RED}Invalid key: {str(e)[:40]}...{Style.RESET_ALL}")

            self.ACCOUNTS = accounts
            self.log(f"Accounts : {Fore.GREEN + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL} {Fore.WHITE}loaded{Style.RESET_ALL}")
            return accounts
        except Exception as e:
            self.log(f"Accounts : {Fore.RED}Error - {str(e)}{Style.RESET_ALL}")
            return []

    def load_proxies(self):
        proxy_file = "proxy.txt"
        try:
            if not os.path.exists(proxy_file):
                self.log(f"Proxies  : {Fore.YELLOW}File not found, creating...{Style.RESET_ALL}")
                with open(proxy_file, "w") as f:
                    f.write("# One proxy per line (optional)\n")
                return []

            with open(proxy_file, "r") as f:
                lines = f.readlines()

            proxies = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)

            self.PROXIES = proxies
            self.log(f"Proxies  : {Fore.GREEN + Style.BRIGHT}{len(proxies)}{Style.RESET_ALL} {Fore.WHITE}loaded{Style.RESET_ALL}")
            return proxies
        except Exception as e:
            self.log(f"Proxies  : {Fore.RED}Error - {str(e)}{Style.RESET_ALL}")
            return []

    def build_proxy_config(self, proxy_url):
        try:
            if not proxy_url:
                return None, None

            if proxy_url.startswith("http://") or proxy_url.startswith("https://"):
                return proxy_url, proxy_url
            elif proxy_url.startswith("socks5://"):
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy_url)
                return proxy_url, connector
            else:
                full_url = f"http://{proxy_url}"
                return full_url, full_url
        except Exception as e:
            self.log(f"Proxy    : {Fore.RED}Build error - {str(e)}{Style.RESET_ALL}")
            return None, None

    def get_next_proxy_for_account(self, account_index):
        if not self.PROXIES:
            return None

        proxy_index = account_index % len(self.PROXIES)
        proxy_url = self.PROXIES[proxy_index]
        return proxy_url

    async def check_connection(self):
        try:
            w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
            connected = w3.is_connected()
            if connected:
                block = w3.eth.block_number
                self.log(f"RPC      : {Fore.GREEN}Connected{Style.RESET_ALL} | Block: {Fore.WHITE + Style.BRIGHT}{block}{Style.RESET_ALL}")
                self.W3 = w3
                return True
            else:
                self.log(f"RPC      : {Fore.RED}Connection failed{Style.RESET_ALL}")
                return False
        except Exception as e:
            self.log(f"RPC      : {Fore.RED}Error - {str(e)}{Style.RESET_ALL}")
            return False

    async def get_sp_status(self, wallet, retries=5):
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.API_BASE}/api/zpoints/user/{wallet}"
                    async with session.get(url) as response:
                        data = await response.json()
                        stats = data.get("stats", {})
                        result = {
                            "sp": float(stats.get("totalPoints", 0)),
                            "rank": data.get("rank", 0),
                            "trades": int(stats.get("totalTrades", 0)),
                            "volume": float(stats.get("totalVolume", 0)),
                            "today_sp": float(data.get("todaySpEarned", 0)),
                        }
                        self.log(
                            f"SP Status: {Fore.GREEN}{result['sp']:,.0f} SP{Style.RESET_ALL} | "
                            f"Rank: {Fore.WHITE + Style.BRIGHT}#{result['rank']}{Style.RESET_ALL} | "
                            f"Today: {Fore.BLUE + Style.BRIGHT}{result['today_sp']:,.0f}{Style.RESET_ALL}"
                        )
                        return result
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(f"SP Status: {Fore.RED}Failed{Style.RESET_ALL} - {Fore.YELLOW}{str(e)}{Style.RESET_ALL}")
        return None

    async def check_balance(self, wallet, token_addr, retries=5):
        for attempt in range(retries):
            try:
                def _check():
                    token = self.W3.eth.contract(
                        address=Web3.to_checksum_address(token_addr),
                        abi=self.ERC20_ABI
                    )
                    return token.functions.balanceOf(Web3.to_checksum_address(wallet)).call()

                balance = await asyncio.to_thread(_check)
                return balance
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(f"Balance  : {Fore.RED}Failed{Style.RESET_ALL} - {Fore.YELLOW}{str(e)}{Style.RESET_ALL}")
        return 0

    async def approve_if_needed(self, wallet, private_key, token_addr, spender, amount, retries=5):
        for attempt in range(retries):
            try:
                def _approve():
                    token = self.W3.eth.contract(
                        address=Web3.to_checksum_address(token_addr),
                        abi=self.ERC20_ABI
                    )
                    allowance = token.functions.allowance(
                        Web3.to_checksum_address(wallet),
                        Web3.to_checksum_address(spender)
                    ).call()

                    if allowance < amount:
                        tx = token.functions.approve(
                            Web3.to_checksum_address(spender),
                            2**256 - 1
                        ).build_transaction({
                            "from": Web3.to_checksum_address(wallet),
                            "nonce": self.W3.eth.get_transaction_count(Web3.to_checksum_address(wallet)),
                            "gas": 100000,
                            "gasPrice": self.W3.eth.gas_price,
                        })
                        signed = self.W3.eth.account.sign_transaction(tx, private_key)
                        tx_hash = self.W3.eth.send_raw_transaction(signed.raw_transaction)
                        receipt = self.W3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                        return {"status": "approved", "tx_hash": tx_hash.hex(), "receipt": receipt}
                    else:
                        return {"status": "already_approved"}

                result = await asyncio.to_thread(_approve)
                return result
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(f"Approve  : {Fore.RED}Failed{Style.RESET_ALL} - {Fore.YELLOW}{str(e)}{Style.RESET_ALL}")
        return None

    async def execute_swap(self, wallet, private_key, token_in, token_out, amount_in, retries=5):
        for attempt in range(retries):
            try:
                def _swap():
                    router = self.W3.eth.contract(
                        address=Web3.to_checksum_address(self.ROUTER),
                        abi=self.ROUTER_ABI
                    )

                    amount_out = router.functions.getAmountOut(
                        Web3.to_checksum_address(token_in),
                        Web3.to_checksum_address(token_out),
                        amount_in
                    ).call()

                    min_amount_out = int(amount_out * 0.999)

                    tx = router.functions.swap(
                        Web3.to_checksum_address(token_in),
                        Web3.to_checksum_address(token_out),
                        amount_in,
                        min_amount_out
                    ).build_transaction({
                        "from": Web3.to_checksum_address(wallet),
                        "nonce": self.W3.eth.get_transaction_count(Web3.to_checksum_address(wallet)),
                        "gas": 500000,
                        "gasPrice": self.W3.eth.gas_price,
                    })

                    signed = self.W3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = self.W3.eth.send_raw_transaction(signed.raw_transaction)
                    receipt = self.W3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    return {"tx_hash": tx_hash.hex(), "receipt": receipt, "amount_out": amount_out}

                result = await asyncio.to_thread(_swap)
                return result
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(f"Swap     : {Fore.RED}Failed{Style.RESET_ALL} - {Fore.YELLOW}{str(e)}{Style.RESET_ALL}")
        return None

    async def process_accounts(self, option):
        if not self.ACCOUNTS:
            self.log(f"{Fore.RED}No accounts loaded{Style.RESET_ALL}")
            return

        connected = await self.check_connection()
        if not connected:
            return

        for idx, account in enumerate(self.ACCOUNTS):
            wallet = account["address"]
            private_key = account["private_key"]

            self.log(
                f"{Fore.MAGENTA + Style.BRIGHT}{'─' * 50}{Style.RESET_ALL}"
            )
            self.log(
                f"Account  : {Fore.WHITE + Style.BRIGHT}{wallet}{Style.RESET_ALL}"
            )

            # Assign proxy
            proxy = self.get_next_proxy_for_account(idx)
            if proxy:
                proxy_url, proxy_config = self.build_proxy_config(proxy)
                self.log(
                    f"Proxy    : {Fore.BLUE + Style.BRIGHT}{proxy_url}{Style.RESET_ALL}"
                )

            if option == "1" or option == "4":
                await self.get_sp_status(wallet)

            if option == "2" or option == "4":
                amount_wei = self.SWAP_AMOUNT * 10 ** self.DECIMALS
                for name, addr in self.TOKENS.items():
                    if name != "USDZ":
                        self.log(
                            f"Approve  : {Fore.BLUE}{name}{Style.RESET_ALL} -> Router"
                        )
                        result = await self.approve_if_needed(
                            wallet, private_key, addr, self.AMM, amount_wei * 100
                        )
                        if result and result["status"] == "approved":
                            self.log(
                                f"Approve  : {Fore.GREEN}Approved{Style.RESET_ALL} | "
                                f"TX: {Fore.WHITE + Style.BRIGHT}{result['tx_hash'][:20]}...{Style.RESET_ALL}"
                            )
                        elif result and result["status"] == "already_approved":
                            self.log(
                                f"Approve  : {Fore.GREEN}Already approved{Style.RESET_ALL}"
                            )

            if option == "3" or option == "4":
                await self.process_volume_farm(wallet, private_key)

    async def process_volume_farm(self, wallet, private_key):
        self.log(
            f"{'─' * 50}"
        )
        self.log(
            f"Farming  : {Fore.BLUE + Style.BRIGHT}Starting volume farm...{Style.RESET_ALL}"
        )

        status = await self.get_sp_status(wallet)
        if not status:
            self.log(f"Farming  : {Fore.RED}Cannot get SP status{Style.RESET_ALL}")
            return

        if status["today_sp"] >= self.DAILY_CAP:
            self.log(
                f"Farming  : {Fore.GREEN}Daily cap reached!{Style.RESET_ALL} | "
                f"SP: {Fore.WHITE + Style.BRIGHT}{status['today_sp']:,.0f}{Style.RESET_ALL}"
            )
            return

        sp_remaining = self.DAILY_CAP - status["today_sp"]
        volume_needed = sp_remaining * 100
        swaps_needed = int(volume_needed / self.SWAP_AMOUNT) + 1

        self.log(
            f"Farming  : {Fore.WHITE + Style.BRIGHT}{swaps_needed}{Style.RESET_ALL} swaps needed "
            f"@ ${Fore.WHITE + Style.BRIGHT}{self.SWAP_AMOUNT:,}{Style.RESET_ALL}"
        )

        amount_wei = self.SWAP_AMOUNT * 10 ** self.DECIMALS
        total_swaps = 0
        total_volume = 0

        for i in range(swaps_needed):
            if total_swaps > 0 and total_swaps % 10 == 0:
                status = await self.get_sp_status(wallet)
                if status and status["today_sp"] >= self.DAILY_CAP:
                    self.log(
                        f"Farming  : {Fore.GREEN}Daily cap reached!{Style.RESET_ALL} | "
                        f"SP: {Fore.WHITE + Style.BRIGHT}{status['today_sp']:,.0f}{Style.RESET_ALL}"
                    )
                    break

            self.log(
                f"Round    : {Fore.WHITE + Style.BRIGHT}{i + 1}{Style.RESET_ALL}/{Fore.WHITE + Style.BRIGHT}{swaps_needed}{Style.RESET_ALL}"
            )

            usdt_bal = await self.check_balance(wallet, self.TOKENS["USDT"])
            swap_amt = min(usdt_bal, amount_wei)

            if swap_amt > 0:
                self.log(
                    f"Swap     : {Fore.BLUE}USDT{Style.RESET_ALL} -> {Fore.BLUE}USDZ{Style.RESET_ALL} | "
                    f"${Fore.WHITE + Style.BRIGHT}{swap_amt / 10 ** 18:,.0f}{Style.RESET_ALL}"
                )
                result = await self.execute_swap(
                    wallet, private_key,
                    self.TOKENS["USDT"], self.TOKENS["USDZ"],
                    swap_amt
                )
                if result:
                    if result["receipt"].status == 1:
                        self.log(
                            f"Swap     : {Fore.GREEN}Success{Style.RESET_ALL} | "
                            f"TX: {Fore.WHITE + Style.BRIGHT}{result['tx_hash'][:20]}...{Style.RESET_ALL} | "
                            f"Gas: {Fore.WHITE + Style.BRIGHT}{result['receipt'].gasUsed}{Style.RESET_ALL}"
                        )
                        total_swaps += 1
                        total_volume += swap_amt / 10 ** 18
                    else:
                        self.log(
                            f"Swap     : {Fore.RED}Failed{Style.RESET_ALL} | "
                            f"TX: {Fore.WHITE + Style.BRIGHT}{result['tx_hash'][:20]}...{Style.RESET_ALL}"
                        )

            await asyncio.sleep(2)

            usdz_bal = await self.check_balance(wallet, self.TOKENS["USDZ"])
            if usdz_bal > 0:
                self.log(
                    f"Swap     : {Fore.BLUE}USDZ{Style.RESET_ALL} -> {Fore.BLUE}USDT{Style.RESET_ALL} | "
                    f"${Fore.WHITE + Style.BRIGHT}{usdz_bal / 10 ** 18:,.0f}{Style.RESET_ALL}"
                )
                result = await self.execute_swap(
                    wallet, private_key,
                    self.TOKENS["USDZ"], self.TOKENS["USDT"],
                    usdz_bal
                )
                if result:
                    if result["receipt"].status == 1:
                        self.log(
                            f"Swap     : {Fore.GREEN}Success{Style.RESET_ALL} | "
                            f"TX: {Fore.WHITE + Style.BRIGHT}{result['tx_hash'][:20]}...{Style.RESET_ALL} | "
                            f"Gas: {Fore.WHITE + Style.BRIGHT}{result['receipt'].gasUsed}{Style.RESET_ALL}"
                        )
                        total_swaps += 1
                        total_volume += usdz_bal / 10 ** 18
                    else:
                        self.log(
                            f"Swap     : {Fore.RED}Failed{Style.RESET_ALL} | "
                            f"TX: {Fore.WHITE + Style.BRIGHT}{result['tx_hash'][:20]}...{Style.RESET_ALL}"
                        )

            await asyncio.sleep(2)

        self.log(
            f"Farming  : {Fore.GREEN}Done{Style.RESET_ALL} | "
            f"Swaps: {Fore.WHITE + Style.BRIGHT}{total_swaps}{Style.RESET_ALL} | "
            f"Volume: ${Fore.WHITE + Style.BRIGHT}{total_volume:,.0f}{Style.RESET_ALL}"
        )

    async def main(self):
        self.welcome()

        while True:
            print()
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ MENU ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} ══════════════════════════════════{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN + Style.BRIGHT}[1]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} Check SP Status{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN + Style.BRIGHT}[2]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} Approve Tokens{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN + Style.BRIGHT}[3]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} Volume Farm (Auto-Swap){Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN + Style.BRIGHT}[4]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} Run All Features{Style.RESET_ALL}"
            )
            print()

            choice = self.print_question("Select option")

            if choice not in ["1", "2", "3", "4"]:
                self.log(f"{Fore.RED}Invalid option{Style.RESET_ALL}")
                continue

            self.load_accounts()
            self.load_proxies()

            await self.process_accounts(choice)

            print()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}All tasks completed{Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.YELLOW + Style.BRIGHT}Press Ctrl+C to exit{Style.RESET_ALL}"
            )
            print()


if __name__ == "__main__":
    try:
        bot = StabilizerFinance()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"[ EXIT ] Stabilizer Finance - BOT")
