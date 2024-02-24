from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import streamlit as st
import requests
import json
import os


def get_members(view_name=None):
    print("getting members")
    access_token = st.secrets["airtable"]["personal_access_token"]
    url, headers = "https://api.airtable.com/v0/appnc2IWGpsHNfTvt/Members", {"Authorization": f"Bearer {access_token}"}
    params = {} if view_name is None else {"view": view_name}
    members = []
    while True:
        res = requests.get(url, headers=headers, params=params).json()
        members += res.get('records', [])
        if 'offset' not in res: break
        params['offset'] = res['offset']
    return members


def get_build_updates(view_name=None):
    print("getting build updates")
    access_token = st.secrets["airtable"]["personal_access_token"]
    url, headers = "https://api.airtable.com/v0/appnc2IWGpsHNfTvt/Build Updates", {
        "Authorization": f"Bearer {access_token}"}
    params = {} if view_name is None else {"view": view_name}
    updates = []
    while True:
        res = requests.get(url, headers=headers, params=params).json()
        updates += res.get('records', [])
        if 'offset' not in res: break
        params['offset'] = res['offset']
    return updates


def create_embedding(member_text):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    response = client.embeddings.create(
        input=member_text,
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
            member["profile_image"] = image_path
    else:
        member["profile_image"] = ""


def save_members(new_members_to_process):
    if new_members_to_process:
        existing_members = []
        if os.path.exists('members.py'):
            with open('members.py', 'r') as f:
                try:
                    existing_members = eval(f.read().strip())
                except (SyntaxError, NameError):
                    pass

        existing_members.extend(new_members_to_process)

        with open('members.py', 'w') as f:
            f.write("members = " + json.dumps(existing_members, indent=4))

        print(f"New members added to file: {len(new_members_to_process)}")
    else:
        print("No new members to process.")

def find_new_members(updated_members, existing_members_ids):
    new_members_to_process = [member for member in updated_members if member['id'] not in existing_members_ids]
    return new_members_to_process

def process_member(member, current_index, total_members):
    if 'Name' not in member['fields'] or not member['fields']['Name']:
        print(f"Skipping member with ID {member['id']} as their name is missing.")
        return ""

    save_member_image(member)
    member_name = member['fields']['Name']
    updates = get_build_updates()
    building = member["fields"].get("What will you build", "")
    past_work = member["fields"].get("Past work", "")
    text_representation = f"Name: {member_name}, currently building: {building}, past work: {past_work}"

    member_updates = [update for update in updates if member_name.lower() in update['fields'].get('Full name', '').lower()]

    total_updates = len(member_updates)
    print(f"Processing {total_updates} build updates for member: {member_name}")
    print(f"Currently processing member {current_index} out of {total_members}")

    member_projects = {}

    for idx, update in enumerate(member_updates, start=1):
        print(f"Processing update {idx} out of {total_updates}")

        project_name = update['fields'].get('Project', update['fields'].get('😊 Build project name', ""))
        if not project_name:
            continue  # Skip this update if neither key is present

        if project_name not in member_projects:
            member_projects[project_name] = {'build_updates': []}

        clean_update_data = {
            "member_id": member['id'],
            "date": update["fields"].get("Build update date", ""),
            "build_update": update["fields"].get("🏗 Build goal for week", ""),
            "build_url": update['fields'].get("🚢 Build URL", ""),
            "asks": update['fields'].get("Would you like to submit a help request or have any asks from community?", ""),
            "customers_talked_to": update['fields'].get("How many customers did you test with this week?", ""),
            "milestones": update['fields'].get("Did you reach a key milestone you want to share?", "")
        }

        clean_update_data["build_update_embeddings"] = create_embedding(clean_update_data["build_update"])

        member_projects[project_name]['build_updates'].append(clean_update_data)

    projects_array = [{"project_name": project, "details": details} for project, details in member_projects.items()]

    return {
        "id": member["id"],
        "profile_picture": f"member_images/{member['id']}.png",
        "name": member_name,
        "building": building,
        "past_work": past_work,
        "linkedin_url": member["fields"].get("What's the link to your LinkedIn?", ""),
        "areas_of_expertise": member["fields"].get("What are your areas of expertise you have (select max 4 please)", ""),
        "member_text_representation": text_representation,
        "member_embedding": create_embedding(text_representation),
        "projects": projects_array
    }

if __name__ == "__main__":
    members = get_members("Accepted only")
    members = members
    total_members = len(members)
    print(f"Total members to process: {total_members}")

    existing_members_ids = set()

    try:
        with open('members.py', 'r') as file:
            data = file.read()
            existing_members = json.loads(data)
            existing_members_ids.update(member['id'] for member in existing_members)
    except FileNotFoundError:
        pass

    new_members_to_process = find_new_members(members, existing_members_ids)

    with ThreadPoolExecutor() as executor:
        results = []
        for index, member in enumerate(new_members_to_process, start=1):
            result = executor.submit(process_member, member, index, len(new_members_to_process))
            results.append(result)

        processed_members = [result.result() for result in results]

    save_members(processed_members)
