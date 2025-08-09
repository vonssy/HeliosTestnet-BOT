from web3 import Web3
from web3.exceptions import TransactionNotFound
from solcx import compile_source, install_solc, set_solc_version
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

install_solc('0.8.20')
set_solc_version('0.8.20')

class Helios:
    def __init__(self) -> None:
        self.BASE_API = "https://testnet-api.helioschain.network/api"
        self.RPC_URL = "https://testnet1.helioschainlabs.org/"
        self.HLS_CONTRACT_ADDRESS = "0xD4949664cD82660AaE99bEdc034a0deA8A0bd517"
        self.WETH_CONTRACT_ADDRESS = "0x80b5a32E4F032B2a058b4F29EC95EEfEEB87aDcd"
        self.WBNB_CONTRACT_ADDRESS = "0xd567B3d7B8FE3C79a1AD8dA978812cfC4Fa05e75"
        self.BRIDGE_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000900"
        self.DELEGATE_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000800"
        self.REWARDS_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000801"
        self.PROPOSAL_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000805"
        self.CHRONOS_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000830"
        self.DEST_TOKENS = [
            { "Ticker": "Sepolia", "ChainId": 11155111 },
            { "Ticker": "BSC Testnet", "ChainId": 97 }
        ]
        self.VALIDATATORS = [
            # {"Moniker": "Helios-Hedge", "Contract Address": "0x007a1123a54cdD9bA35AD2012DB086b9d8350A5f"},
            {"Moniker": "Helios-Peer", "Contract Address": "0x72a9B3509B19D9Dbc2E0Df71c4A6451e8a3DD705"},
            {"Moniker": "Helios-Unity", "Contract Address": "0x7e62c5e7Eba41fC8c25e605749C476C0236e0604"},
            {"Moniker": "Helios-Supra", "Contract Address": "0xa75a393FF3D17eA7D9c9105d5459769EA3EAEf8D"},
            {"Moniker": "Helios-Inter", "Contract Address": "0x882f8A95409C127f0dE7BA83b4Dfa0096C3D8D79"}
        ]
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},
            {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}
        ]''')
        self.HELIOS_CONTRACT_ABI = [
            {
                "name": "sendToChain",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "name": "chainId", "type": "uint64", "internalType": "uint64" },
                    { "name": "destAddress", "type": "string", "internalType": "string" },
                    { "name": "contractAddress", "type": "address", "internalType": "address" },
                    { "name": "amount", "type": "uint256", "internalType": "uint256" },
                    { "name": "bridgeFee", "type": "uint256", "internalType": "uint256" }
                ],
                "outputs": [
                    { "name": "success", "type": "bool", "internalType": "bool" }
                ]
            },
            {
                "name": "delegate",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "delegatorAddress", "type": "address" },
                    { "internalType": "address", "name": "validatorAddress", "type": "address" },
                    { "internalType": "uint256", "name": "amount", "type": "uint256" },
                    { "internalType": "string", "name": "denom", "type": "string" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "name": "claimRewards",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "delegatorAddress", "type": "address" },
                    { "internalType": "uint32", "name": "maxRetrieve", "type": "uint32" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "type": "function",
                "name": "hyperionProposal",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "string", "name": "title", "type": "string" },
                    { "internalType": "string", "name": "description", "type": "string" },
                    { "internalType": "string", "name": "msg", "type": "string" },
                    { "internalType": "uint256", "name": "initialDepositAmount", "type": "uint256" }
                ],
                "outputs": [
                    { "internalType": "uint64", "name": "proposalId", "type": "uint64" }
                ]
            },
            {
                "name": "vote",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "voter", "type": "address" },
                    { "internalType": "uint64", "name": "proposalId", "type": "uint64" },
                    { "internalType": "enum VoteOption", "name": "option", "type": "uint8" },
                    { "internalType": "string", "name": "metadata", "type": "string" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "type": "function",
                "name": "createCron",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "contractAddress", "type": "address" },
                    { "internalType": "string", "name": "abi", "type": "string" },
                    { "internalType": "string", "name": "methodName", "type": "string" },
                    { "internalType": "string[]", "name": "params", "type": "string[]" },
                    { "internalType": "uint64", "name": "frequency", "type": "uint64" },
                    { "internalType": "uint64", "name": "expirationBlock", "type": "uint64" },
                    { "internalType": "uint64", "name": "gasLimit", "type": "uint64" },
                    { "internalType": "uint256", "name": "maxGasPrice", "type": "uint256" },
                    { "internalType": "uint256", "name": "amountToDeposit", "type": "uint256" },
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" },
                ]
            }
        ]
        self.PAGE_URL = "https://testnet.helioschain.network"
        self.SITE_KEY = "0x4AAAAAABhz7Yc1no53_eWA"
        self.CAPTCHA_KEY = None
        self.BASE_HEADERS = {}
        self.PORTAL_HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.used_nonce = {}
        self.bridge_count = 0
        self.bridge_amount = 0
        self.delegate_count = 0
        self.hls_delegate_amount = 0
        self.weth_delegate_amount = 0
        self.wbnb_delegate_amount = 0
        self.create_proposal = False
        self.proposal_title = None
        self.proposal_description = None
        self.proposal_deposit = 0
        self.vote_count = 0
        self.deploy_count = 0
        self.cron_count = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Helios Testnet{Fore.BLUE + Style.BRIGHT} Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_2captcha_key(self):
        try:
            with open("2captcha_key.txt", 'r') as file:
                captcha_key = file.read().strip()

            return captcha_key
        except Exception as e:
            return None
    
    async def load_proxies(self, use_proxy_choice: bool):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Address Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}                  "
            )
            return None
        
    def generate_payload(self, account: str, address: str):
        try:
            message = f"Welcome to Helios! Please sign this message to verify your wallet ownership.\n\nWallet: {address}"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            payload = {
                "wallet": address,
                "signature": signature
            }

            return payload
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Req Payload Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}                  "
            )
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    def generate_random_asset(self):
        asset = random.choice([
            self.HLS_CONTRACT_ADDRESS,
            self.WETH_CONTRACT_ADDRESS,
            self.WBNB_CONTRACT_ADDRESS
        ])

        if asset == self.HLS_CONTRACT_ADDRESS:
            denom = "ahelios"
            ticker = "HLS"
            amount = self.hls_delegate_amount
        elif asset == self.WETH_CONTRACT_ADDRESS:
            denom = "hyperion-11155111-0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
            ticker = "WETH"
            amount = self.weth_delegate_amount
        else:
            denom = "hyperion-97-0xC689BF5a007F44410676109f8aa8E3562da1c9Ba"
            ticker = "WBNB"
            amount = self.wbnb_delegate_amount

        return asset, ticker, denom, amount
        
    def generate_raw_token(self):
        numbers = random.randint(0, 99999)
        token_name = f"Token{numbers}"
        token_symbol = f"T{numbers}"
        raw_supply = random.randint(1000, 1_000_000)
        total_supply = raw_supply * (10 ** 18)

        return token_name, token_symbol, raw_supply, total_supply
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
            
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Send TX Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
        
    async def get_token_balance(self, address: str, contract_address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
            balance = token_contract.functions.balanceOf(address).call()
            decimals = token_contract.functions.decimals().call()

            token_balance = balance / (10 ** decimals)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
    
    async def approving_token(self, account: str, address: str, spender_address: str, contract_address: str, estimated_fees: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            spender = web3.to_checksum_address(spender_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
            decimals = token_contract.functions.decimals().call()

            amount_to_wei = int(self.bridge_amount * (10 ** decimals)) + estimated_fees

            allowance = token_contract.functions.allowance(address, spender).call()
            if allowance < amount_to_wei:
                approve_data = token_contract.functions.approve(spender, amount_to_wei)

                latest_block = web3.eth.get_block("latest")
                base_fee = latest_block.get("baseFeePerGas", 0)
                max_priority_fee = web3.to_wei(1.111, "gwei")
                max_fee = base_fee + max_priority_fee

                approve_tx = approve_data.build_transaction({
                    "from": address,
                    "gas": 1500000,
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id,
                })

                tx_hash = await self.send_raw_transaction_with_retries(account, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
                block_number = receipt.blockNumber
                self.used_nonce[address] += 1
                
                explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
                
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Approve  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
                )
                await asyncio.sleep(10)
            
            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")

    async def perform_bridge(self, account: str, address: str, dest_chain_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            bridge_amount = web3.to_wei(self.bridge_amount, "ether")
            estimated_fees = int(0.5 * (10 ** 18))

            await self.approving_token(account, address, self.BRIDGE_ROUTER_ADDRESS, self.HLS_CONTRACT_ADDRESS, estimated_fees, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.BRIDGE_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            bridge_data = token_contract.functions.sendToChain(
                dest_chain_id, address, self.HLS_CONTRACT_ADDRESS, bridge_amount, estimated_fees
            )

            estimated_gas = bridge_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = max_priority_fee

            bridge_tx = bridge_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, bridge_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_delegate(self, account: str, address: str, contract_address: str, denom: str, delegate_amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.DELEGATE_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            amount = web3.to_wei(delegate_amount, "ether")

            delegate_data = token_contract.functions.delegate(address, contract_address, amount, denom)

            estimated_gas = delegate_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            delegate_tx = delegate_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, delegate_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_claim_rewards(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.REWARDS_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            claim_data = token_contract.functions.claimRewards(address, 10)

            estimated_gas = claim_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            claim_tx = claim_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, claim_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_create_proposal(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            msg = json.dumps({
                "@type": "/helios.hyperion.v1.MsgUpdateOutTxTimeout", 
                "signer": address, 
                "chain_id": random.choice([11155111, 97]), 
                "target_batch_timeout": 3600000, 
                "target_outgoing_tx_timeout": 3600000
            })

            amount_to_wei = web3.to_wei(self.proposal_deposit, "ether")

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.PROPOSAL_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            proposal_data = token_contract.functions.hyperionProposal(self.proposal_title, self.proposal_description, msg, amount_to_wei)

            estimated_gas = proposal_data.estimate_gas({"from": address, "value":amount_to_wei})

            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            proposal_tx = proposal_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, proposal_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
        
    async def perform_vote_proposal(self, account: str, address: str, proposal_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.PROPOSAL_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            metadata = f"Vote on proposal {proposal_id}"

            vote_data = token_contract.functions.vote(address, proposal_id, 1, metadata)

            estimated_gas = vote_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            vote_tx = vote_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, vote_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_deploy_contract(self, account: str, address: str, token_name: str, token_symbol: str, total_supply: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            source_code = f'''
            // SPDX-License-Identifier: MIT
            pragma solidity ^0.8.20;

            contract MyToken {{
                string public name = "{token_name}";
                string public symbol = "{token_symbol}";
                uint8 public decimals = 18;
                uint256 public totalSupply;

                mapping(address => uint256) public balanceOf;
                mapping(address => mapping(address => uint256)) public allowance;

                event Transfer(address indexed from, address indexed to, uint256 value);
                event Approval(address indexed owner, address indexed spender, uint256 value);

                constructor() {{
                    totalSupply = {total_supply};
                    balanceOf[msg.sender] = totalSupply;
                    emit Transfer(address(0), msg.sender, totalSupply);
                }}

                function transfer(address to, uint256 value) public returns (bool) {{
                    require(balanceOf[msg.sender] >= value, "Insufficient balance");
                    balanceOf[msg.sender] -= value;
                    balanceOf[to] += value;
                    emit Transfer(msg.sender, to, value);
                    return true;
                }}

                function approve(address spender, uint256 value) public returns (bool) {{
                    allowance[msg.sender][spender] = value;
                    emit Approval(msg.sender, spender, value);
                    return true;
                }}

                function transferFrom(address from, address to, uint256 value) public returns (bool) {{
                    require(balanceOf[from] >= value, "Insufficient balance");
                    require(allowance[from][msg.sender] >= value, "Allowance exceeded");
                    balanceOf[from] -= value;
                    balanceOf[to] += value;
                    allowance[from][msg.sender] -= value;
                    emit Transfer(from, to, value);
                    return true;
                }}
            }}
            '''

            compiled_sol = compile_source(source_code, output_values=["abi", "bin"])
            contract_id, contract_interface = compiled_sol.popitem()
            abi = contract_interface['abi']
            bytecode = contract_interface['bin']
            TokenContract = web3.eth.contract(abi=abi, bytecode=bytecode)

            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = max_priority_fee

            tx = TokenContract.constructor().build_transaction({
                "from": address,
                "gas": 3000000,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority_fee,
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            contract_address = receipt.contractAddress
            self.used_nonce[address] += 1

            return tx_hash, block_number, contract_address

        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None, None
        
    async def perform_create_cron(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.CHRONOS_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            current_block = web3.eth.block_number

            contract_address = web3.to_checksum_address("0xaece8330ae7aeecc6a5e59b9d1ccca02f2dc6c38")
            abi = "[{\"inputs\":[],\"name\":\"increment\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"}]"
            method_name = "increment"
            params = []
            frequency = 300
            expiration_block = current_block + 10000
            gas_limit = 110000
            max_gas_price = 5000000000
            amount_to_deposit = web3.to_wei(1, "ether")

            cron_data = token_contract.functions.createCron(
                contract_address, abi, method_name, params, frequency, expiration_block, gas_limit, max_gas_price, amount_to_deposit
            )

            estimated_gas = cron_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            cron_tx = cron_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, cron_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    def print_bridge_question(self):
        while True:
            try:
                bridge_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Bridge Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if bridge_count > 0:
                    self.bridge_count = bridge_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Bridge Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                bridge_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Bridge Amount (HLS) -> {Style.RESET_ALL}").strip())
                if bridge_amount > 0:
                    self.bridge_amount = bridge_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Bridge Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

    def print_delegate_question(self):
        while True:
            try:
                delegate_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Delegate Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if delegate_count > 0:
                    self.delegate_count = delegate_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Delegate Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                hls_delegate_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Delegate Amount (HLS) -> {Style.RESET_ALL}").strip())
                if hls_delegate_amount > 0:
                    self.hls_delegate_amount = hls_delegate_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Delegate Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
        while True:
            try:
                weth_delegate_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Delegate Amount (WETH) -> {Style.RESET_ALL}").strip())
                if weth_delegate_amount > 0:
                    self.weth_delegate_amount = weth_delegate_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Delegate Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
        while True:
            try:
                wbnb_delegate_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Delegate Amount (WBNB) -> {Style.RESET_ALL}").strip())
                if wbnb_delegate_amount > 0:
                    self.wbnb_delegate_amount = wbnb_delegate_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Delegate Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
    def print_create_question(self):
       while True:
            proposal_title = str(input(f"{Fore.YELLOW + Style.BRIGHT}Input a Title For Proposal (eg. Vonssy) -> {Style.RESET_ALL}").strip())
            if proposal_title:
                self.proposal_title = proposal_title
                break
            else:
                print(f"{Fore.RED + Style.BRIGHT}Proposal Title Cannot be Empty.{Style.RESET_ALL}")
       
       while True:
            proposal_description = str(input(f"{Fore.YELLOW + Style.BRIGHT}Input a Description For Proposal (eg. Long Live's Vonssy!!!) -> {Style.RESET_ALL}").strip())
            if proposal_description:
                self.proposal_description = proposal_description
                break
            else:
                print(f"{Fore.RED + Style.BRIGHT}Proposal Description Cannot be Empty.{Style.RESET_ALL}")
       
       while True:
            try:
                proposal_deposit = float(input(f"{Fore.YELLOW + Style.BRIGHT}Proposal Initial Deposit Amount [Min. 1 HLS] -> {Style.RESET_ALL}").strip())
                if proposal_deposit >= 1:
                    self.proposal_deposit = proposal_deposit
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Proposal Initial Deposit Amount must be >= 1.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
    
    def print_proposal_question(self):
       while True:
            try:
                create_proposal = str(input(f"{Fore.YELLOW + Style.BRIGHT}Create a Proposal? [y/n] -> {Style.RESET_ALL}").strip())
                if create_proposal in ["y", "n"]:
                    self.create_proposal = create_proposal == "y"
                    if self.create_proposal:
                        self.print_create_question()
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Proposal Initial Deposit Amount must be >= 1.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
    
    def print_vote_question(self):
        while True:
            try:
                vote_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Vote Proposal Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if vote_count > 0:
                    self.vote_count = vote_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Vote Proposal Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
    
    def print_deploy_question(self):
        while True:
            try:
                deploy_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Deploy Contract Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if deploy_count > 0:
                    self.deploy_count = deploy_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Deploy Contract Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
    
    def print_cron_question(self):
        while True:
            try:
                cron_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Deploy Chronos Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if cron_count > 0:
                    self.cron_count = cron_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Deploy Chronos Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Max Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
         
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Claim HLS Faucet{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Bridge HLS Funds{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Delegate Random Validators{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Claim Delegate Rewards{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}5. Create Governance Proposal{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}6. Vote Governance Proposal{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}7. Deploy Token Contract{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}8. Deploy Chronos Scheduled{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}9. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3/4/5] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                    option_type = (
                        "Claim HLS Faucet" if option == 1 else 
                        "Bridge HLS Funds" if option == 2 else 
                        "Delegate Random Validators" if option == 3 else 
                        "Claim Delegate Rewards" if option == 4 else 
                        "Create Governance Proposal" if option == 5 else 
                        "Vote Governance Proposal" if option == 6 else 
                        "Deploy Token Contract" if option == 7 else 
                        "Deploy Chronos Scheduled" if option == 8 else 
                        "Run All Features"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, 4, 5, 6, 7, 8, or 9.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, 4, 5, 6, 7, 8, or 9).{Style.RESET_ALL}")
        
        if option == 2:
            self.print_bridge_question()
            self.print_delay_question()

        elif option == 3:
            self.print_delegate_question()
            self.print_delay_question()

        elif option == 5:
            self.print_create_question()

        elif option == 6:
            self.print_vote_question()
            self.print_delay_question()

        elif option == 7:
            self.print_deploy_question()
            self.print_delay_question()

        elif option == 8:
            self.print_cron_question()
            self.print_delay_question()
            
        elif option == 9:
            self.print_bridge_question()
            self.print_delegate_question()
            self.print_proposal_question()
            self.print_vote_question()
            self.print_deploy_question()
            self.print_cron_question()
            self.print_delay_question()

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Free Proxyscrape Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Free Proxyscrape" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, choose, rotate
    
    async def solve_cf_turnstile(self, retries=5):
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=60)) as session:

                    if self.CAPTCHA_KEY is None:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                            f"{Fore.RED+Style.BRIGHT}Turnstile Not Solved{Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT}2Captcha Key Is None{Style.RESET_ALL}"
                        )
                        return None
                    
                    url = f"http://2captcha.com/in.php?key={self.CAPTCHA_KEY}&method=turnstile&sitekey={self.SITE_KEY}&pageurl={self.PAGE_URL}"
                    async with session.get(url=url) as response:
                        response.raise_for_status()
                        result = await response.text()

                        if 'OK|' not in result:
                            self.log(
                                f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.BLUE+Style.BRIGHT}Message :{Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}{result}{Style.RESET_ALL}"
                            )
                            await asyncio.sleep(5)
                            continue

                        request_id = result.split('|')[1]

                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT}Req Id  :{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {request_id} {Style.RESET_ALL}"
                        )

                        for _ in range(30):
                            res_url = f"http://2captcha.com/res.php?key={self.CAPTCHA_KEY}&action=get&id={request_id}"
                            async with session.get(url=res_url) as res_response:
                                res_response.raise_for_status()
                                res_result = await res_response.text()

                                if 'OK|' in res_result:
                                    turnstile_token = res_result.split('|')[1]
                                    return turnstile_token
                                elif res_result == "CAPCHA_NOT_READY":
                                    self.log(
                                        f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                                        f"{Fore.BLUE+Style.BRIGHT}Message :{Style.RESET_ALL}"
                                        f"{Fore.YELLOW + Style.BRIGHT} Captcha Not Ready {Style.RESET_ALL}"
                                    )
                                    await asyncio.sleep(5)
                                    continue
                                else:
                                    break

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT}Turnstile Not Solved{Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT}{str(e)}{Style.RESET_ALL}"
                )
                return None
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    async def user_login(self, account: str, address: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/users/login"
        data = json.dumps(self.generate_payload(account, address))
        headers = {
            **self.BASE_HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Message   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def check_eligibility(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/faucet/check-eligibility"
        data = json.dumps({"token":"HLS", "chain":"helios-testnet"})
        headers = {
            **self.BASE_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} GET Eligibility Status Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def request_faucet(self, address: str, turnstile_token: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/faucet/request"
        data = json.dumps({"token":"HLS", "chain":"helios-testnet", "amount":1, "turnstileToken":turnstile_token})
        headers = {
            **self.BASE_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def proposal_lists(self, address: str, use_proxy: bool, retries=5):
        data = json.dumps({
            "jsonrpc":"2.0",
            "method":"eth_getProposalsByPageAndSize",
            "params":["0x1","0x14"],
            "id":1
        })
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=self.RPC_URL, headers=self.PORTAL_HEADERS[address], data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Proposal Lists Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    continue

                return False
            
            return True
    
    async def process_user_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            login = await self.user_login(account, address, use_proxy)
            if login and login.get("success", False):
                self.access_tokens[address] = login["token"]

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
                )
                return True

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
            )
            return False
        
    async def process_fetch_proposal(self, address: str, use_proxy: bool):
        propsal_lists = await self.proposal_lists(address, use_proxy)
        if not propsal_lists: return False

        proposals = propsal_lists.get("result", [])
        
        live_proposals = [
            p for p in proposals
            if p.get("status") == "VOTING_PERIOD"
        ]

        if not live_proposals: 
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} No Available Proposals {Style.RESET_ALL}"
            )
            return False

        used_proposals = random.choice(live_proposals)

        return used_proposals
        
    async def process_perform_bridge(self, account: str, address: str, dest_chain_id: int, use_proxy: bool):
        tx_hash, block_number = await self.perform_bridge(account, address, dest_chain_id, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_delegate(self, account: str, address: str, contract_address: str, denom: str, amount: float, use_proxy: bool):
        tx_hash, block_number = await self.perform_delegate(account, address, contract_address, denom, amount, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_claim_rewards(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_claim_rewards(account, address, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_create_proposal(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_create_proposal(account, address, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_vote_proposal(self, account: str, address: str, proposal_id: int, use_proxy: bool):
        tx_hash, block_number = await self.perform_vote_proposal(account, address, proposal_id, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_deploy_contract(self, account: str, address: str, token_name: str, token_symbol: str, total_supply: int, use_proxy: bool):
        tx_hash, block_number, contract_address = await self.perform_deploy_contract(account, address, token_name, token_symbol, total_supply, use_proxy)
        if tx_hash and block_number and contract_address:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Contract :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {contract_address} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_create_cron(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_create_cron(account, address, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_option_1(self, address: str, use_proxy: bool):
        check = await self.check_eligibility(address, use_proxy)
        if check and check.get("success", False):
            is_eligible = check.get("isEligible", False)

            if is_eligible:
                self.log(f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}")

                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT}Solving Captcha Turnstile...{Style.RESET_ALL}"
                )

                turnstile_token = await self.solve_cf_turnstile()
                if turnstile_token:
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}Message :{Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT} Capctha Turnstile Solved Successfully{Style.RESET_ALL}"
                    )

                    request = await self.request_faucet(address, turnstile_token, use_proxy)
                    if request and request.get("success", False):
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT} 1 HLS Faucet Claimed Successfully {Style.RESET_ALL}"
                        )

            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Not Eligible to Claim {Style.RESET_ALL}"
                )

    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Bridge    :{Style.RESET_ALL}")

        for i in range(self.bridge_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.bridge_count}{Style.RESET_ALL}                                   "
            )

            balance = await self.get_token_balance(address, self.HLS_CONTRACT_ADDRESS, use_proxy)

            destination = random.choice(self.DEST_TOKENS)
            ticker = destination["Ticker"]
            dest_chain_id = destination["ChainId"]
            estimated_fee = 0.5

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Option   :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} Helios to {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} HLS {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.bridge_amount} HLS {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Est. Fee :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {estimated_fee} HLS {Style.RESET_ALL}"
            )

            required = self.bridge_amount + estimated_fee

            if not balance or balance <= required:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient HLS Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_bridge(account, address, dest_chain_id, use_proxy)
            await self.print_timer()

    async def process_option_3(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Delegate  :{Style.RESET_ALL}                       ")

        for i in range(self.delegate_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.delegate_count}{Style.RESET_ALL}                                   "
            )

            asset, ticker, denom, amount = self.generate_random_asset()

            validators = random.choice(self.VALIDATATORS)
            moniker = validators["Moniker"]
            contract_address = validators["Contract Address"]

            balance = await self.get_token_balance(address, asset, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Asset    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Validator:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {moniker} {Style.RESET_ALL}"
            )

            if not balance or balance <= amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                continue
            
            await self.process_perform_delegate(account, address, contract_address, denom, amount, use_proxy)
            await self.print_timer()

    async def process_option_4(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Rewards   :{Style.RESET_ALL}                       ")
        
        await self.process_perform_claim_rewards(account, address, use_proxy)
        await self.print_timer()

    async def process_option_5(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Create    :{Style.RESET_ALL}                       ")

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Title    :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.proposal_title} {Style.RESET_ALL}"
        )

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Desc     :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.proposal_description} {Style.RESET_ALL}"
        )

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Deposit  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.proposal_deposit} HLS {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address, self.HLS_CONTRACT_ADDRESS, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} HLS {Style.RESET_ALL}"
        )
        if not balance or balance <= self.proposal_deposit:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient HLS Token Balance {Style.RESET_ALL}"
            )
            return
        
        await self.process_perform_create_proposal(account, address, use_proxy)
        await self.print_timer()

    async def process_option_6(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Vote      :{Style.RESET_ALL}                       ")
        for i in range(self.vote_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.vote_count}{Style.RESET_ALL}                                   "
            )

            proposals = await self.process_fetch_proposal(address, use_proxy)
            if not proposals: continue

            proposal_id = proposals["id"]
            title = proposals["title"]
            proposer = proposals["proposer"]

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Prop. Id :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proposal_id} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Title    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {title} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Proposer :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {proposer} {Style.RESET_ALL}"
            )
            
            await self.process_perform_vote_proposal(account, address, proposal_id, use_proxy)
            await self.print_timer()

    async def process_option_7(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Deploy    :{Style.RESET_ALL}                       ")

        for i in range(self.deploy_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.deploy_count}{Style.RESET_ALL}                                   "
            )

            token_name, token_symbol, raw_supply, total_supply = self.generate_raw_token()

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Name     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {token_name} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Symbol   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {token_symbol} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Decimals :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} 18 {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Supply   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {raw_supply} {Style.RESET_ALL}"
            )
            
            await self.process_perform_deploy_contract(account, address, token_name, token_symbol, total_supply, use_proxy)
            await self.print_timer()

    async def process_option_8(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Chronos   :{Style.RESET_ALL}                       ")

        for i in range(self.cron_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.cron_count}{Style.RESET_ALL}                                   "
            )
            
            await self.process_perform_create_cron(account, address, use_proxy)
            await self.print_timer()

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_user_login(account, address, use_proxy, rotate_proxy)
        if logined:
            web3 = await self.get_web3_with_check(address, use_proxy)
            if not web3:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Web3 Not Connected {Style.RESET_ALL}"
                )
                return
            
            self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")

            if option == 1:
                await self.process_option_1(address, use_proxy)

            elif option == 2:
                await self.process_option_2(account, address, use_proxy)

            elif option == 3:
                await self.process_option_3(account, address, use_proxy)

            elif option == 4:
                await self.process_option_4(account, address, use_proxy)

            elif option == 5:
                await self.process_option_5(account, address, use_proxy)

            elif option == 6:
                await self.process_option_6(account, address, use_proxy)

            elif option == 7:
                await self.process_option_7(account, address, use_proxy)

            elif option == 8:
                await self.process_option_8(account, address, use_proxy)

            elif option == 9:
                await self.process_option_1(address, use_proxy)
                await asyncio.sleep(5)

                await self.process_option_2(account, address, use_proxy)
                await asyncio.sleep(5)
                
                await self.process_option_3(account, address, use_proxy)
                await asyncio.sleep(5)
                
                await self.process_option_4(account, address, use_proxy)
                await asyncio.sleep(5)
                
                if self.create_proposal:
                    await self.process_option_5(account, address, use_proxy)
                    await asyncio.sleep(5)
                
                await self.process_option_6(account, address, use_proxy)
                await asyncio.sleep(5)
                
                await self.process_option_7(account, address, use_proxy)
                await asyncio.sleep(5)
                
                await self.process_option_8(account, address, use_proxy)
                await asyncio.sleep(5)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            capctha_key = self.load_2captcha_key()
            if capctha_key:
                self.CAPTCHA_KEY = capctha_key

            option, use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        user_agent = FakeUserAgent().random

                        self.BASE_HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://testnet.helioschain.network",
                            "Referer": "https://testnet.helioschain.network/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": user_agent
                        }

                        self.PORTAL_HEADERS[address] = {
                            "Content-Type": "application/json",
                            "Referer": "https://portal.helioschain.network/",
                            "User-Agent": user_agent
                        }

                        await self.process_accounts(account, address, option, use_proxy_choice, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Helios()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Helios - BOT{Style.RESET_ALL}                                       "                              
        )