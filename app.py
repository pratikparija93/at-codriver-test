import streamlit as st
from backend import run_agentic_workflow

st.title("AutoTrader Co-Driver (Agentic Edition)")

uploaded_file = st.file_uploader("Upload Vehicle Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Generate Co-Driver Listing"):
        with st.spinner("Agent is analyzing image, querying DB, and writing text..."):
            image_bytes = uploaded_file.getvalue()
            
            # Now we unpack BOTH variables returned from the backend
            thinking_steps, draft_text = run_agentic_workflow(image_bytes)
            
            st.success("Generation Complete!")
            
            # --- NEW: Display the thinking steps ---
            with st.expander("🧠 View Agent Thinking Process", expanded=True):
                for step in thinking_steps:
                    st.markdown(step)
            
            st.text_area("Draft Advertisement:", draft_text, height=150)
            
            if st.button("Approve & Publish to Live DB"):
                st.balloons()
                st.success("Successfully POSTed to Live Advertisement Database!")