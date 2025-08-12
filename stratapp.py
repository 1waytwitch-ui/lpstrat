import streamlit as st
from web3 import Web3
from decimal import Decimal
import requests
import pandas as pd

# ---------- CONFIGURATION ----------
BASE_RPC_URL = 'https://mainnet.base.org'  # Pas besoin de clé API
ERC20_ABI = '''
[
  {"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
  {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
  {"constant":true,"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}
]
'''

# Connexion Web3
web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))


# ---------- OUTILS ----------
def to_checksum(addr):
    """Corrige l’adresse au format EIP-55 si besoin."""
    return Web3.to_checksum_address(addr.strip())


# ---------- FONCTIONS ----------
@st.cache_data
def get_token_info(address):
    contract = web3.eth.contract(address=address, abi=ERC20_ABI)
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    return symbol, decimals

@st.cache_data
def get_pool_balances(pool_address, token_a, token_b):
    contract_a = web3.eth.contract(address=token_a, abi=ERC20_ABI)
    contract_b = web3.eth.contract(address=token_b, abi=ERC20_ABI)
    balance_a = contract_a.functions.balanceOf(pool_address).call()
    balance_b = contract_b.functions.balanceOf(pool_address).call()
    return balance_a, balance_b

@st.cache_data
def get_token_prices(ids=['ethereum', 'usd-coin']):
    ids_param = ','.join(ids)
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd'
    res = requests.get(url).json()
    return {k: Decimal(str(v['usd'])) for k, v in res.items()}

def calculate_impermanent_loss(price_change_ratio):
    sqrt_ratio = Decimal(price_change_ratio).sqrt()
    hodl = (1 + price_change_ratio) / 2
    lp_value = sqrt_ratio * 2 / (1 + sqrt_ratio)
    il = 1 - (lp_value / hodl)
    return float(il * 100)


# ---------- INTERFACE STREAMLIT ----------
st.title("🔍 Analyse de Stratégie LP (Uniswap/Base)")

st.sidebar.header("⚙️ Paramètres")

# Exemple : Uniswap V3 WETH / USDbC sur Base
example_pool = "0xF46f64f157c2cD6136D4a052Ea938bD6fEb3e26C"
example_token_a = "0x4200000000000000000000000000000000000006"  # WETH
example_token_b = "0xd9aa594f868a0a2e2efc5663ec3083a1b5dcb6c8"  # USDbC

# Bouton d'exemple
if st.sidebar.button("Utiliser un exemple"):
    st.session_state["pool_address"] = example_pool
    st.session_state["token_a"] = example_token_a
    st.session_state["token_b"] = example_token_b
else:
    st.session_state.setdefault("pool_address", "")
    st.session_state.setdefault("token_a", "")
    st.session_state.setdefault("token_b", "")

# Champs de saisie
pool_address = st.sidebar.text_input("Adresse du Pool", st.session_state["pool_address"])
token_a = st.sidebar.text_input("Adresse du Token A", st.session_state["token_a"])
token_b = st.sidebar.text_input("Adresse du Token B", st.session_state["token_b"])


# ---------- ANALYSE ----------
if st.sidebar.button("Analyser"):
    try:
        # ✅ Corriger les adresses au format checksum
        pool_address = to_checksum(pool_address)
        token_a = to_checksum(token_a)
        token_b = to_checksum(token_b)

        # Infos tokens
        symbol_a, decimals_a = get_token_info(token_a)
        symbol_b, decimals_b = get_token_info(token_b)

        # Balances dans le pool
        raw_a, raw_b = get_pool_balances(pool_address, token_a, token_b)
        balance_a = Decimal(raw_a) / Decimal(10) ** decimals_a
        balance_b = Decimal(raw_b) / Decimal(10) ** decimals_b

        # Prix via CoinGecko
        prices = get_token_prices(['ethereum', 'usd-coin'])
        price_a = prices['ethereum']
        price_b = prices['usd-coin']

        # TVL
        tvl = (balance_a * price_a) + (balance_b * price_b)

        # IL simulée (ex : prix doublé)
        il = calculate_impermanent_loss(2.0)

        st.success("✅ Données récupérées avec succès")

        data = {
            "Token A": symbol_a,
            "Token B": symbol_b,
            "Balance A": float(balance_a),
            "Balance B": float(balance_b),
            "Prix A (USD)": float(price_a),
            "Prix B (USD)": float(price_b),
            "TVL (USD)": float(tvl),
            "IL simulée (%)": il
        }

        df = pd.DataFrame(data.items(), columns=["Métrique", "Valeur"])
        st.table(df)

    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
