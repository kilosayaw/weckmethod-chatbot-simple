import streamlit as st
import pandas as pd
import re # For more flexible keyword matching

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads product and YouTube data from CSVs."""
    try:
        products_df = pd.read_csv("RMTS Agent Data - Products.csv")
        youtube_df = pd.read_csv("RMTS Agent Data - YouTube Links.csv")
        return products_df, youtube_df
    except FileNotFoundError:
        st.error("Error: Make sure 'RMTS Agent Data - Products.csv' and 'RMTS Agent Data - YouTube Links.csv' are in the same directory.")
        return pd.DataFrame(), pd.DataFrame() # Return empty DFs on error

products_df, youtube_df = load_data()

# --- Chatbot Logic (UPDATED) ---
def get_simple_chatbot_response(user_query, products_df, youtube_df):
    """
    Finds relevant products and lists multiple associated videos based on keywords.
    """
    if products_df.empty or youtube_df.empty:
        return "Sorry, the product data could not be loaded. Please check the data files."

    user_keywords = [word.lower() for word in re.findall(r'\b\w+\b', user_query) if len(word) > 2]
    
    # Filter products based on our new enhanced keywords
    relevant_products = []
    for _, product in products_df.iterrows():
        product_text = f"{product['ProductName'].lower()} {str(product.get('RelatedKeywords', '')).lower()}".strip()
        
        if any(keyword in product_text for keyword in user_keywords):
            relevant_products.append(product)

    if not relevant_products:
        return "I'm sorry, I couldn't find any products that match your query. Could you try asking in a different way? For example, ask about 'improving my golf swing' or 'core strength'."

    # Build a more detailed response
    responses = ["Based on your request, I found these matching products and training videos for you:"]

    for product in relevant_products:
        product_name = product['ProductName']
        product_url = product['ProductURL']
        product_id = product['ProductID']

        # Find all related YouTube videos for this product
        related_videos = youtube_df[
            youtube_df['ProductID'].astype(str).str.contains(str(product_id), case=False, na=False)
        ]
        
        # Start building the response for this specific product
        product_response = f"### {product_name}\n"
        product_response += f"This product is a great choice for what you're looking for. You can learn more and purchase it here:\n"
        product_response += f"➡️ **[{product_name} Product Page]({product_url})**\n"

        # NEW: Add up to 3 videos instead of just one
        if not related_videos.empty:
            product_response += "\nHere are some popular training videos to get you started:\n"
            video_links = []
            # Loop through the first 3 videos found
            for _, video in related_videos.head(3).iterrows():
                video_title = video['VideoTitle']
                video_url = video['VideoURL']
                video_links.append(f"- [{video_title}]({video_url})")
            
            product_response += "\n".join(video_links)
        else:
            product_response += "\n_I couldn't find a specific training video for this product, but check out the WeckMethod YouTube channel for hundreds of tutorials!_"
        
        responses.append(product_response)
            
    return "\n\n---\n\n".join(responses) # Use a separator for multiple products

# --- Streamlit App Layout (No changes needed here, but included for completeness) ---
st.set_page_config(layout="wide")
st.title("🏋️ WeckMethod Product & Training Assistant")
st.markdown("### Ask me about WeckMethod products!")
st.info("Example questions: 'What can I use for footwork?', 'Tell me about the BOSU Elite', 'Do you have anything for strength training?'")

col1, col2 = st.columns([2, 1])

with col1:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you find the right WeckMethod product today?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What are you looking for?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Finding the best recommendations..."):
                response = get_simple_chatbot_response(prompt, products_df, youtube_df)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    st.header("Raw Data Preview")
    st.subheader("WeckMethod Products")
    st.dataframe(products_df, height=300)
    st.subheader("WeckMethod YouTube Links")
    st.dataframe(youtube_df, height=300)
