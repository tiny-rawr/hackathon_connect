from concurrent.futures import ThreadPoolExecutor
import json
import os
import requests
import streamlit as st
from openai import OpenAI
import base64


def get_records(table_name="Members", view_name=None):
    print(f"Retrieving {table_name.lower()}...")
    access_token = st.secrets["airtable"]["personal_access_token"]
    url = f"https://api.airtable.com/v0/appdxzy7MxhBwI8WY/{table_name}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {} if view_name is None else {"view": view_name}
    items = []
    while True:
        res = requests.get(url, headers=headers, params=params).json()
        items += res.get("records", [])
        if "offset" not in res:
            break
        params["offset"] = res["offset"]
    return items

def create_embedding(text):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def save_member_image(member):
    member_fields = member["fields"]
    image_url = member_fields.get("Profile picture", [{}])[0].get("url")

    if image_url:
        image_path = os.path.join("member_images", f"{member['id']}.png")
        if not os.path.exists(image_path):
            image_response = requests.get(image_url)
            if image_response.ok:
                with open(image_path, "wb") as image_file:
                    image_file.write(image_response.content)
                member["profile_image"] = image_path
            else:
                print(f"Failed to download image for member ID {member['id']}")
                member["profile_image"] = ""
        else:
            print(f"Image file already exists for member ID {member['id']}")
            member["profile_image"] = ""
    else:
        member["profile_image"] = ""

def save_members(new_members_to_process):
    if new_members_to_process:
        existing_members = []
        if os.path.exists("members.py"):
            with open("members.py", "r") as f:
                try:
                    members_file = f.read()
                    members_dict = {}
                    exec(members_file, members_dict)
                    existing_members = members_dict.get("members", [])
                except (SyntaxError, NameError):
                    pass

        existing_members.extend(new_members_to_process)

        with open("members.py", "w") as f:
            f.write("members = ")
            json.dump(existing_members, f, indent=4, default=lambda x: "" if x is None else x)

        print(f"New members added to file: {len(new_members_to_process)}")
    else:
        print("No new members to process.")

def find_new_members(updated_members, existing_members_ids):
    new_members_to_process = [member for member in updated_members if member["id"] not in existing_members_ids]
    return new_members_to_process

def process_member(member, current_index, total_members):
    if "Name" not in member["fields"] or not member["fields"]["Name"]:
        print(f"Skipping member with ID {member['id']} as their name is missing.")
        return ""

    save_member_image(member)
    member_name = member["fields"]["Name"]
    projects = get_records("Projects")

    text_representation = f"Name: {member_name}, Areas of Expertise: {member['fields'].get('What are your areas of expertise and interest?', '')}, Entry Type: {member['fields'].get('Team or individual entry type', '')}, Looking for Team Members: {member['fields'].get('Looking for more team members?', '')}, Dietary Requirements: {member['fields'].get('Dietary requirements', '')}"

    member_project = next((project for project in projects if member["id"] in project["fields"]["Team members"]), None)

    if member_project:
        project_fields = member_project["fields"]
        team_member_names = [project_fields["Name (from Team members)"][i] for i in range(len(project_fields["Team members"]))]
        project_text_representation = f"Name: {project_fields['Name']}, Notes: {project_fields['Notes']}, Team member names: {', '.join(team_member_names)}, Project name: {project_fields['Project name']}, What project does: {project_fields['Describe what your product solves in 2-3 scentences']}, Applicable bounty challenges: {', '.join(project_fields['Applicable bounty challenges'])}, City: {project_fields['City']}"
        project_embedding = create_embedding(project_text_representation)

        # Download and encode video as base64
        video_url = project_fields.get('3 minute demo video (describe the problem you are solving + walk through of solution build)', [{}])[0].get('url', '')
        if video_url:
            video_response = requests.get(video_url)
            if video_response.ok:
                video_base64 = base64.b64encode(video_response.content).decode('utf-8')
            else:
                print(f"Failed to download video for project ID {member_project['id']}")
                video_base64 = ""
        else:
            video_base64 = ""
    else:
        project_text_representation = ""
        project_embedding = ""
        video_base64 = ""

    member_data = {
        "id": member["id"],
        "profile_picture": f"member_images/{member['id']}.png",
        "name": member_name,
        "bio": member["fields"].get("Bio: Current professional role and why you want to enter", ""),
        "linkedin_url": member["fields"].get("What's the link to your LinkedIn?", ""),
        "twitter_url": member["fields"].get("Twitter", ""),
        "email": member["fields"].get("Email", ""),
        "areas_of_expertise": member["fields"].get("What are your areas of expertise and interest?", ""),
        "entry_type": member["fields"].get("Team or individual entry type", ""),
        "looking_for_team_members": member["fields"].get("Looking for more team members?", ""),
        "dietary_requirements": member["fields"].get("Dietary requirements", ""),
        "member_text_representation": text_representation,
        "project_text_representation": project_text_representation,
        "project_details": member_project["fields"] if member_project else "",
        "combined_embedding": create_embedding(f"{text_representation} {project_text_representation}"),
        "video_base64": video_base64
    }

    return member_data

if __name__ == "__main__":
    members = get_records("Members")
    total_members = len(members)
    print(f"Total members to process: {total_members}")

    existing_members_ids = set()

    try:
        with open("members.py", "r") as file:
            data = file.read()
            members_dict = {}
            exec(data, members_dict)
            existing_members = members_dict.get("members", [])
            existing_members_ids = set(member["id"] for member in existing_members if isinstance(member, dict))
    except FileNotFoundError:
        existing_members_ids = set()

    new_members_to_process = find_new_members(members, existing_members_ids)

    with ThreadPoolExecutor() as executor:
        results = []
        for index, member in enumerate(new_members_to_process, start=1):
            result = executor.submit(process_member, member, index, len(new_members_to_process))
            results.append(result)

        processed_members = [result.result() for result in results]

    save_members(processed_members)