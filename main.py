import streamlit as st
from members import members
from get_members import create_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
import os
from streamlit_pills import pills
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
    .image-container-small img {
        border-radius: 50%;
        width: 20px;
        height: 20px;
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
    .linkedin_link {
        color: black !important;
    }
    .linkedin_link:hover {
        color: #188CFE !important;
    }
    .build-update {
      box-sizing: border-box;
      padding: 1rem;
      background-color: #EFF9FE;
      border-radius: 10px;
      margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header():
    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image("logo.png")

    st.markdown("<h1 style='text-align: center; margin-top: -1.5rem;'>Welcome to Build Zone!</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center;'>Builders rise by lifting each other and to do this, you need to find each other. For the Build Together hackathon, we are launching the POC of this and can't wait to see what you do!</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center;'>Built with ❤️ and ☕️ by <a href='https://www.linkedin.com/in/becca9941/' target='_blank'>Becca</a> (would love feedback).</p>",
        unsafe_allow_html=True)

def display_project(project_details):
    if not isinstance(project_details, dict):
        print("Skipping project: Invalid project details.")
        return

    project_name = project_details.get('Project name', '')
    project_description = project_details.get('Describe what your product solves in 2-3 scentences', '')
    applicable_bounties = project_details.get('Applicable bounty challenges', [])
    team_members = project_details.get('Name (from Team members)', [])
    team_emails = project_details.get('Email (from Email)', [])
    video_url = project_details.get('3 minute demo video (describe the problem you are solving + walk through of solution build)', [{}])[0].get('url', '')

    st.video(video_url)
    st.write(f"**{project_name}**")
    st.write(f"{project_description}")

    if team_members:
        st.write(f"**Team Members:** {', '.join(team_members)}")

    st.write("---")  # Add a horizontal line separator

def display_projects(members):
    unique_projects = set()
    all_projects = []

    for member in members:
        if isinstance(member, dict) and 'project_details' in member:
            project_details = member['project_details']
            if isinstance(project_details, dict):
                project_name = project_details.get('Project name', '')
                if project_name not in unique_projects:
                    unique_projects.add(project_name)
                    all_projects.append(project_details)
            else:
                print(f"Skipping member: project_details is not a dictionary: {project_details}")
        else:
            print("Skipping member: No project details found.")

    num_projects = len(all_projects)
    num_cols = 2  # Display 2 projects side by side

    for i in range(0, num_projects, num_cols):
        cols = st.columns(num_cols)
        for j, col in enumerate(cols):
            project_index = i + j
            if project_index < num_projects:
                with col:
                    display_project(all_projects[project_index])

def display_member(member):
    if not isinstance(member, dict) or 'profile_picture' not in member:
        print("Skipping member: No profile picture found.")
        return
    profile_image = get_image_base64(member['profile_picture'])

    name = member["name"]
    skills = member["areas_of_expertise"]
    bio = member.get('bio', '').encode('utf-8', 'ignore').decode('utf-8')
    entry_type = member.get('entry_type', '').encode('utf-8', 'ignore').decode('utf-8')
    industries = ', '.join(member.get('areas_of_expertise', [])).encode('utf-8', 'ignore').decode('utf-8')
    weird_fact = member.get('dietary_requirements', '').encode('utf-8', 'ignore').decode('utf-8')
    looking_for_team_members = member.get('looking_for_team_members', '').encode('utf-8', 'ignore').decode('utf-8')
    team_members = []
    if member.get('project_details'):
        team_members_data = member['project_details'].get('Team members', [])
        team_member_names = [get_member_name(team_member_id, members) for team_member_id in team_members_data]
        team_members = [name.encode('utf-8', 'ignore').decode('utf-8') for name in team_member_names if name]

    linkedin_url = member.get('linkedin_url', '')
    if not linkedin_url:
        linkedin_url = member.get('twitter_url', '')

    col1, col2 = st.columns([1, 3])
    with col1:
        if profile_image:
            st.markdown(f"<div class='image-container'><img src='{profile_image}'></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span>**<a class='linkedin_link' href='{linkedin_url}'>{name}</a>**</span><br>", unsafe_allow_html=True)
        skills_html = ''.join([f"<span class='skill-chip'>{skill}</span>" for skill in skills])
        st.markdown(skills_html, unsafe_allow_html=True)
        st.write(f"**Bio:** {bio}")
        if team_members:
          st.write(f"**Team Members:** {', '.join(team_members)}")
        st.write(f"**Looking for Team Members:** {looking_for_team_members}")
    st.markdown("---")

def get_member_name(member_id, members):
    for member in members:
        if member['id'] == member_id:
            return member['name']
    return None

    st.markdown("---")

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def retrieve_and_rank(query_embedding, items, embedding_key):
    valid_items = [item for item in items if isinstance(item, dict) and embedding_key in item]
    similarities = [(item, cosine_similarity(query_embedding, item[embedding_key])) for item in valid_items]
    sorted_items = sorted(similarities, key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items]

def retrieve_and_rank_build_updates(query_embedding, members, embedding_key):
    valid_build_updates = []
    for member in members:
        if "projects" in member:
            for project in member["projects"]:
                if "build_updates" in project["details"]:
                    for build_update in project["details"]["build_updates"]:
                        if embedding_key in build_update:
                            valid_build_updates.append({
                                "member_name": member["name"],
                                "member_picture": get_image_base64(member["profile_picture"]),
                                "build_update": build_update,
                                "project_name": project['project_name'],
                                "similarity": cosine_similarity(query_embedding, build_update[embedding_key])
                            })

    sorted_build_updates = sorted(valid_build_updates, key=lambda x: x["similarity"], reverse=True)
    return sorted_build_updates



def rag_query():
    query = st.text_area("", placeholder="🔍 Search members by asking things like: 'Who's working in law?', 'Who is passionate about RAG?'")
    submit = st.button("Search")

    if submit:
        query_embedding = create_embedding(query)

        top_members = retrieve_and_rank(query_embedding, members, 'member_embedding')
        top_build_updates = retrieve_and_rank_build_updates(query_embedding, members, 'build_update_embeddings')

        tab1, tab2 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS"])

        with tab1:
            st.subheader("Top members who match your search")
            for member in top_members[:20]:
                display_member(member)
        with tab2:
            st.subheader("Top projects that match your search")
            unique_projects = set()
            for update in top_build_updates[:20]:
                unique_projects.add(update['project_name'])
            for member in members:
                if not isinstance(member, dict):
                    print("Skipping member: Not a dictionary.")
                    continue
                projects = member.get("projects", [])
                if projects:
                    for project in projects:
                        if not isinstance(member, dict) or 'profile_picture' not in member:
                            print("Skipping member: No profile picture found.")
                            return
                        profile_image = get_image_base64(member['profile_picture'])
                        for project_name in list(unique_projects)[:20]:
                          if project_name == project["project_name"]:
                              updates = project["details"]["build_updates"]
                              with st.expander(f"🚀 {project['project_name'].upper()} | By {member['name']}", expanded=True):
                                  col1, col2 = st.columns([1, 3])
                                  with col1:
                                      if profile_image:
                                          st.markdown(f"<div class='image-container'><img src='{profile_image}'></div>",
                                                      unsafe_allow_html=True)
                                  with col2:
                                      st.subheader(project['project_name'])
                                      st.markdown(f"By [{member['name']}]({member['linkedin_url']})")
                                  if updates:
                                      st.write("")
                                      st.write(f"**Updates (x {len(updates)})**:")
                                      for update in updates:
                                          display_build_update(update)

        return True

    return False

def paginate_members(members):
    if "page_number" not in st.session_state:
        st.session_state.page_number = 1

    items_per_page = 20
    total_pages = (len(members) - 1) // items_per_page + 1

    # Ensure the page number is within the valid range
    if st.session_state.page_number > total_pages:
        st.session_state.page_number = total_pages

    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page
    displayed_members = members[start_idx:end_idx]

    for member in displayed_members:
        display_member(member)

    # Use a min and max value to constrain the slider within valid limits
    page_number = None  # Initialize page_number as None
    if total_pages > 1:
        page_number = st.slider("Pages (20 members per page):", min_value=1, max_value=total_pages, value=st.session_state.page_number)
    else:
        # If there is only one page, don't show the slider
        st.write(f"Page 1 of {total_pages}")

    if page_number is not None and st.session_state.page_number != page_number:
        st.session_state.page_number = page_number
        st.experimental_rerun()

def choose_data_type():
    st.write("")
    tab1, tab2 = st.tabs(["👩‍💻 BUILDERS", "🚀 PROJECTS"])

    with tab1:
        left_column, right_column = st.columns([2, 1])

        with left_column:
            st.subheader("Build Zone")

        with right_column:
            st.markdown('<a style="float: right; background-color: #1765FF; color: white; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="https://join.slack.com/t/buildtogether-x1i6405/shared_invite/zt-2k0ev4aj8-KezF5NrYieTUBBmJY_DX_A">🚀 Go to the Slack!</a>',unsafe_allow_html=True)

        selected_skill = pills("Connect with other Hackathon participants, find your next build mate:",
                       ["All", "AI Engineer", "Backend Engineer", "Frontend Engineer", "GTM", "Generalist", "Product manager", "Designer", "Domain expert", "IOS/App", "RAG", "DevTools", "Opensource", "Image/Multi-madel", "Ai Agents"],
                       ["🌐", "🤖", "🖥️", "💻", "📈", "🛠️", "📋", "🎨", "📚", "📱", "🔎", "🛠️", "🌍", "🖼️", "👾"], key="selected_skills")

        filtered_members = members
        if selected_skill != "All":
            filtered_members = [member for member in members if isinstance(member, dict) and any(
                skill in member.get("areas_of_expertise", []) for skill in [selected_skill])]

        paginate_members(filtered_members)



    with tab2:
        left_column, right_column = st.columns([2, 1])

        with left_column:
            st.subheader("Hackathon Projects")

        with right_column:
            st.markdown('<a style="float: right; background-color: #1765FF; color: white; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="https://join.slack.com/t/buildtogether-x1i6405/shared_invite/zt-2k0ev4aj8-KezF5NrYieTUBBmJY_DX_A">🚀 Go to the Slack!</a>',unsafe_allow_html=True)

        random.shuffle(members)
        st.write("")
        display_projects(members)


def main():
    display_header()

    if not rag_query():
        choose_data_type()

if __name__ == "__main__":
    main()
