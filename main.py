import streamlit as st
from members import members
from get_members import create_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
import os
from streamlit_pills import pills

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    else:
        with open("member_images/default.png", "rb") as default_image_file:
            encoded_string = base64.b64encode(default_image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"

st.markdown("""
    <style>
    .image-container img {
        border-radius: 50%;
        width: 100px;
        height: 100px;
        object-fit: cover;
    }
    .skill-chip {
        display: inline-block;
        padding: 0 8px;
        margin-right: 2px;
        margin-top: -10px !important;
        font-size: 12px;
        color: white;
        background-color: #BC77FF;
        border-radius: 15px;
    }
    .keyword-chip {
        display: inline-block;
        padding: 0 8px;
        margin-right: 2px;
        margin-top: -10px !important;
        font-size: 12px;
        color: white;
        background-color: #188CFE;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header():
    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image("logo.png")

    st.markdown("<h1 style='text-align: center; margin-top: -1.5rem;'>Member Discovery</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center;'>Use this member search to discover other like-minded builders to connect with. You can also browse member projects and build updates to get an idea of what builders are shipping in real-time!</p>",
        unsafe_allow_html=True)

def display_member(member):
    if not isinstance(member, dict) or 'profile_picture' not in member:
        print("Skipping member: No profile picture found.")
        return
    profile_image = get_image_base64(member['profile_picture'])

    name = member["name"]
    skills = member["areas_of_expertise"]

    col1, col2 = st.columns([1, 3])
    with col1:
        if profile_image:
            st.markdown(f"<div class='image-container'><img src='{profile_image}'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span>**{name}**</span><br>", unsafe_allow_html=True)
        skills_html = ''.join([f"<span class='skill-chip'>{skill}</span>" for skill in skills])
        st.markdown(skills_html, unsafe_allow_html=True)
        st.write(f"**Currently Building:** {member['building']}")
        st.write(f"**Past Work:** {member['past_work']}")

    st.markdown("---")

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def retrieve_and_rank(query_embedding, items, embedding_key):
    valid_items = [item for item in items if isinstance(item, dict) and embedding_key in item]
    similarities = [(item, cosine_similarity(query_embedding, item[embedding_key])) for item in valid_items]
    sorted_items = sorted(similarities, key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items]


def rag_query():
    query = st.text_area("", placeholder="🔍 Search members by asking things like: 'Who's working in law?', 'Who is passionate about RAG?'")
    submit = st.button("Search")

    if submit:
        query_embedding = create_embedding(query)

        # Retrieve and rank members based on the query
        top_members = retrieve_and_rank(query_embedding, members, 'member_embedding')

        tab1, tab2, tab3 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS", "🎯️ BUILD UPDATES"])

        with tab1:
            st.subheader("Top 3 members who match your search")
            for member in top_members[:3]:
                display_member(member)
        with tab2:
            st.subheader("Top 3 projects who match your search")
        with tab3:
            st.subheader("Top 20 build updates who match your search")

        return True

    return False

def paginate_members(members):
    if "page_number" not in st.session_state:
        st.session_state.page_number = 1

    items_per_page = 20
    total_pages = (len(members) - 1) // items_per_page + 1

    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page
    displayed_members = members[start_idx:end_idx]

    for member in displayed_members:
        display_member(member)

    page_number = st.slider("Pages (20 members per page):", 1, total_pages, st.session_state.page_number)

    if st.session_state.page_number != page_number:
        st.session_state.page_number = page_number
        st.experimental_rerun()

def choose_data_type():
    st.write("")
    tab1, tab2, tab3 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS", "🎯️ BUILD UPDATES"])

    with tab1:
        left_column, right_column = st.columns([2, 1])

        with left_column:
            st.subheader("Build Club Members")

        with right_column:
            st.markdown(
                '<a style="float: right; background-color: #1765FF; color: white; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="https://airtable.com/app8eQNdrRqlHBvSi/shr8C5KGPvBqPWkL2">👷‍ Apply to Build Club</a>',
                unsafe_allow_html=True)

        paginate_members(members)

    with tab2:
        left_column, right_column = st.columns([2, 1])

        with left_column:
            st.subheader("Build Club Projects")

        with right_column:
            st.markdown(
                '<a style="float: right; background-color: #1765FF; color: white; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="https://airtable.com/app8eQNdrRqlHBvSi/shrmRqOBpHYhrOTsr">🚀 Start a new project!</a>',
                unsafe_allow_html=True)

    with tab3:
        left_column, right_column = st.columns([2, 1])

        with left_column:
            st.subheader("Build Club Updates")

        with right_column:
            st.markdown(
                '<a style="float: right; background-color: #1765FF; color: white; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="https://airtable.com/app8eQNdrRqlHBvSi/shreowTFIVXILrfN5">🚢 Ship a build update!</a>',
                unsafe_allow_html=True)

# Main function
def main():
    display_header()

    if not rag_query():
        choose_data_type()

if __name__ == "__main__":
    main()
