import streamlit as st
import requests

# URL du Subgraph Uniswap V3 sur Base
UNISWAP_V3_SUBGRAPH_BASE = "https://api.thegraph.com/subgraphs/name/ianlapham/base-v3"

def get_position_data(token_id):
    query = """
    query ($tokenId: ID!) {
      position(id: $tokenId) {
        id
        liquidity
        depositedToken0
        depositedToken1
        withdrawnToken0
        withdrawnToken1
        collectedFeesToken0
        collectedFeesToken1
        token0 {
          id
          symbol
          decimals
        }
        token1 {
          id
          symbol
          decimals
        }
        pool {
          id
          feeTier
          tick
          sqrtPrice
        }
        tickLower {
          tickIdx
        }
        tickUpper {
          tickIdx
        }
      }
    }
    """
    variables = {"tokenId": token_id}
    response = requests.post(UNISWAP_V3_SUBGRAPH_BASE, json={"query": query, "variables": variables})
    data = response.json()
    if 'errors' in data:
        raise Exception(data['errors'])
    return data['data']['position']

st.title("🔍 Analyse de Position LP Uniswap V3 (Base)")

# Input pour token ID (position NFT)
position_token_id = st.text_input("Entrez l'ID de la position NFT Uniswap V3 (ex: '12345')", "")

if st.button("Récupérer les données de la position"):
    if not position_token_id.strip():
        st.error("Merci d'entrer un ID de position valide")
    else:
        try:
            position = get_position_data(position_token_id.strip())
            if not position:
                st.warning("Aucune position trouvée avec cet ID.")
            else:
                st.subheader(f"Position ID : {position['id']}")
                st.write(f"Pool : {position['pool']['id']}")
                st.write(f"Fee Tier : {int(position['pool']['feeTier']) / 10000:.2%}")
                st.write(f"Liquidity : {position['liquidity']}")
                st.write(f"Token0 : {position['token0']['symbol']} ({position['depositedToken0']} déposés)")
                st.write(f"Token1 : {position['token1']['symbol']} ({position['depositedToken1']} déposés)")
                st.write(f"Tick Lower : {position['tickLower']['tickIdx']}")
                st.write(f"Tick Upper : {position['tickUpper']['tickIdx']}")
                st.write(f"Tick actuel : {position['pool']['tick']}")
                st.write(f"sqrtPrice : {position['pool']['sqrtPrice']}")
                st.write(f"Frais collectés Token0 : {position['collectedFeesToken0']}")
                st.write(f"Frais collectés Token1 : {position['collectedFeesToken1']}")
        except Exception as e:
            st.error(f"Erreur : {e}")
