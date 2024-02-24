import streamlit as st
from members import members
from member_data import create_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
import os
import random
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
    profile_image = get_image_base64(f"member_images/{member.get('id')}.png")
    name = member.get("fields", {}).get("Name", "No Name Provided")
    skills = member.get("fields", {}).get("What are your areas of expertise you have (select max 4 please)",
                                          ["No Skills Provided"])
    past_work = member.get("fields", {}).get("Past work", "No Past Work Provided")
    currently_building = member.get("fields", {}).get("What will you build", "No Current Projects Provided")

    col1, col2 = st.columns([1, 3])
    with col1:
        if profile_image:
            st.markdown(f"<div class='image-container'><img src='{profile_image}'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span>**{name}**</span><br>", unsafe_allow_html=True)
        skills_html = ''.join([f"<span class='skill-chip'>{skill}</span>" for skill in skills])
        st.markdown(skills_html, unsafe_allow_html=True)
        st.write(f"**Currently Building:** {currently_building}")
        st.write(f"**Past Work:** {past_work}")

    st.markdown("---")

def retrieve_members(query_embedding, result_limit=3):
    query_embedding = np.array(query_embedding)
    member_embeddings = np.array([member['embeddings'] for member in members])
    similarities = cosine_similarity(query_embedding.reshape(1, -1), member_embeddings)

    # Get indices of top 3 most similar members
    top_indices = similarities.argsort()[0][::-1][:result_limit]

    # Retrieve top 3 members
    top_members = [members[i] for i in top_indices]

    return top_members


def rag_query():
    query = st.text_area("", placeholder="🔍 Search members by asking things like: 'Who's working in law?', 'Who is passionate about RAG?'")
    submit = st.button("Search")

    if submit:
        query_embedding = create_embedding(query)
        top_members = retrieve_members(query_embedding)

        tab1, tab2, tab3 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS", "🎯️ BUILD UPDATES"])

        with tab1:
            st.subheader("Top 3 members who match your search")
            for member in top_members:
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

    page_number = st.slider("Select a page (20 members shown per page):", 1, total_pages, st.session_state.page_number)

    if st.session_state.page_number != page_number:
        st.session_state.page_number = page_number
        st.experimental_rerun()


def choose_data_type():
    st.write("")
    tab1, tab2, tab3 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS", "🎯️ BUILD UPDATES"])

    with tab1:
        st.subheader("Build Club Members")
        st.info(f"""
        👷‍There are {len(members)} total build club members.
        """)
        st.session_state.selected = st.selectbox("Search member by name:",
                                                 ["All"] + [member.get("fields", {}).get("Name", "No Name Provided") for
                                                            member in members], index=0)

        if st.session_state.selected != "All":
            selected_member = next((member for member in members if member.get("fields", {}).get("Name",
                                                                                                 "No Name Provided") == st.session_state.selected),
                                   None)
            if selected_member:
                st.write("")
                display_member(selected_member)
        else:
            selected_skill = pills("Filter members by area of expertise:", ["All", "AI Engineer", "Backend software dev", "Front end software dev", "Product management", "Go to market", "AI / ML specialist researcher", "Designer", "Domain expert", "Idea validating"],
                                ["🔍", "🤖", "💻", "🖥️", "🤹", "🚀", "🔬", "🎨", "🧠", "💡"], key="selected_skills")

            filtered_members = members
            if selected_skill != "All":
                filtered_members = [member for member in members if any(
                    skill in member.get("fields", {}).get("What are your areas of expertise you have (select max 4 please)", []) for skill in [selected_skill])]

            paginate_members(filtered_members)

    with tab2:
        st.subheader("Projects")

    with tab3:
        st.subheader("Build Updates")

def main():
    display_header()

    query_submitted = rag_query()

    if not query_submitted:
        choose_data_type()

if __name__ == "__main__":
    main()
