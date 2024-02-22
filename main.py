import streamlit as st


def display_header():
    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image("logo.png")

    st.markdown("<h1 style='text-align: center; margin-top: -1.5rem;'>Member Discovery</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center;'>Use this member search to discover other like-minded builders to connect with. You can also browse member projects and build updates to get an idea of what builders are shipping in real-time!</p>",
        unsafe_allow_html=True)

def choose_data_type():
    st.write("")
    left_co, cent_co, last_co = st.columns(3)

    with left_co:
        builders = st.button('👩‍💻 BUILDERS', use_container_width=True)

    with cent_co:
        projects = st.button('🚀 PROJECTS', use_container_width=True)

    with last_co:
        build_updates = st.button('🎯️ BUILD UPDATES', use_container_width=True)

    if builders:
        st.write("builders")
    elif projects:
        st.write("projects")
    elif build_updates:
        st.write("build_updates")


def main():
    display_header()
    choose_data_type()


main()
