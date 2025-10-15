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

# --- Chatbot Logic ---
def get_simple_chatbot_response(user_query, products_df, youtube_df):
    """
    Finds relevant products and videos based on simple keyword matching.
    """
    if products_df.empty or youtube_df.empty:
        return "Sorry, the product data could not be loaded. Please check the data files."

    user_keywords = [word.lower() for word in re.findall(r'\b\w+\b', user_query) if len(word) > 2] # Extract keywords, ignore short words
    
    # Filter products based on keywords
    relevant_products = []
    for _, product in products_df.iterrows():
        # Combine ProductName and RelatedKeywords for a comprehensive search text
        product_text = f"{product['ProductName'].lower()} {str(product.get('RelatedKeywords', '')).lower()}".strip()
        
        # Check if any user keyword is in the product's text
        if any(keyword in product_text for keyword in user_keywords):
            relevant_products.append(product)

    responses = []
    if not relevant_products:
        return "I'm sorry, I couldn't find any products related to your query. Try asking about a specific type of equipment like 'rope' or 'balance'."

    responses.append("Here are some WeckMethod products that might help with what you're looking for:")

    for product in relevant_products:
        product_name = product['ProductName']
        product_url = product['ProductURL']
        product_id = product['ProductID']
        product_keywords = str(product.get('RelatedKeywords', 'general training')).lower() # Use a default if keywords are missing

        # Find related YouTube videos for this product
        # Ensure 'ProductID' column in youtube_df is treated as string for contains method
        related_videos = youtube_df[
            youtube_df['ProductID'].astype(str).str.contains(str(product_id), case=False, na=False)
        ]
        
        video_info = ""
        if not related_videos.empty:
            # Pick the first video for simplicity
            video_title = related_videos.iloc[0]['VideoTitle']
            video_url = related_videos.iloc[0]['VideoURL']
            video_info = f"\n\n> _Watch a related training video:_ [{video_title}]({video_url})"
        else:
            video_info = "\n\n> _I couldn't find a specific training video for this product right now, but check out our YouTube channel for more!_"
        
        responses.append(
            f"- **{product_name}**: Great for {product_keywords}. "
            f"\n  *Learn more here:* [{product_url}]({product_url}){video_info}"
        )
            
    return "\n\n".join(responses)

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("🏋️ WeckMethod Product & Training Assistant")
st.markdown("### Ask me about WeckMethod products!")
st.info("Example questions: 'What can I use for footwork?', 'Tell me about the BOSU Elite', 'Do you have anything for strength training?'")

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you find the right WeckMethod product today?"}]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What are you looking for?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Finding the best recommendations..."):
                response = get_simple_chatbot_response(prompt, products_df, youtube_df)
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    st.header("Raw Data Preview")
    st.subheader("WeckMethod Products")
    st.dataframe(products_df, height=300) # Added height for better display
    st.subheader("WeckMethod YouTube Links")
    st.dataframe(youtube_df, height=300) # Added height for better display

# To run this:
# 1. Save your CSV files in the same directory as this script.
# 2. Run `streamlit run app.py` in your terminal.