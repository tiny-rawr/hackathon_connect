import streamlit as st
from members import members
import base64
import os
import random

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

def choose_data_type():
    tab1, tab2, tab3 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS", "🎯️ BUILD UPDATES"])

    with tab1:
        st.session_state.selected_name = st.selectbox("Select a name to filter builders", ["Random 20"] + [member.get("fields", {}).get("Name", "No Name Provided") for member in members], index=0)

        if st.session_state.selected_name != "Random 20":
            selected_member = next((member for member in members if member.get("fields", {}).get("Name", "No Name Provided") == st.session_state.selected_name), None)
            if selected_member:
                st.write("")
                display_member(selected_member)

        else:
            st.write("Showing 20 random Builders")
            random_members = random.sample(members, min(20, len(members)))
            for member in random_members:
                display_member(member)
    with tab2:
        st.write("projects")
    with tab3:
        st.write("build_updates")

def main():
    display_header()
    choose_data_type()

if __name__ == "__main__":
    main()
