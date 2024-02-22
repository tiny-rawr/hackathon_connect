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

def text_representation(member):
    member_fields = member["fields"]
    name = member_fields.get("Name", None)
    building = member_fields.get("What will you build", None)
    past_work = member_fields.get("Past work", None)
    ask = member_fields.get("What do you want to get out of this program?", None)
    expertise = ", ".join(member_fields.get("What are your areas of expertise you have (select max 4 please)", [])) if member_fields.get("What are your areas of expertise you have (select max 4 please)") else None

    member_text = f"{name}\n currently building: {building}\n past work: {past_work}\n ask: {ask}\n expertise: {expertise}"

    return member_text

def create_embedding(member_text):
    client = OpenAI(api_key = st.secrets["openai"]["api_key"])

    response = client.embeddings.create(
        input=member_text,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding

def process_member(index, member, members_count):
    print(f"Processing {index}/{members_count}")
    member["text_representation"] = text_representation(member)
    member["embeddings"] = create_embedding(member["text_representation"])
    return member

def save_member_image(member):
    member_fields = member["fields"]
    image_url = member_fields.get("Profile picture", [{}])[0].get("url")
    if image_url:
        image_response = requests.get(image_url)
        if image_response.ok:
            image_path = os.path.join("member_images", f"{member['id']}.jpg")
            with open(image_path, "wb") as image_file:
                image_file.write(image_response.content)
            member["profile_image"] = image_path
        else:
            print(f"Failed to download image for member ID {member['id']}")
            member["profile_image"] = None
    else:
        member["profile_image"] = None

def save_members_images(members):
    print("saving member images")
    os.makedirs("member_images", exist_ok=True)
    for index, member in enumerate(members, start=1):
        print(f"processing image {index}/{len(members)}")
        save_member_image(member)

def save_members(updated_members):
    with open('members.py', 'w') as f:
        f.write(f"members = {repr(updated_members)}")

def create_members_file(members):
    members_count = len(members)
    updated_members = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(process_member, index, member, members_count) for index, member in enumerate(members)]
        for future in futures:
            updated_members.append(future.result())
    save_members(updated_members)

if __name__ == "__main__":
    members = get_members("Accepted only")
    #save_members_images(members)
    create_members_file(members)
