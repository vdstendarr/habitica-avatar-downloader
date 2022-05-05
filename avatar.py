import json
import os
import platform
import PySimpleGUI as gui
import requests
import threading
import time
from datetime import datetime
from PIL import Image


# Functions
def get_path(add=[""]):
    comp = {"Linux": "/",
            "Windows": "\\"}
    system = platform.system()
    slash = comp[system]
    cpath = __file__.split(slash)[:-1]
    add = add if add != [""] and isinstance(add, list) else []
    finalpath = slash.join(cpath + add)
    return finalpath


def open_json(filepath=None):
    with open(filepath, encoding='utf-8') as jsonfile:
        file = json.load(jsonfile)
    return file


def save_json(dictionary, filepath=None, indent=4):
    with open(filepath, 'w') as jsonfile:
        json.dump(dictionary, jsonfile, indent=indent)


def populate_folders():
	st_folders = []
	for folder in ["avatar", "download", "temp"]:
		if not os.path.isdir(get_path(add=[folder])):
			try:
				os.mkdir(folder)
			except OSError as e:
				print(e)
				exit()
		st_folders.append(get_path(add=[folder]))

	if not os.path.isfile(get_path(add=["settings.json"])):
		settings = {
			"USER_ID": "",
			"API_TOKEN": "",
			"allow_mount": True,
			"allow_pet": True,
			"allow_background": True,
			"allow_costume": True,
			"allow_weapons": True,
			"allow_buggy": True,
			"allow_timestamp": False,
			"is_sleepy": False,
			"temp_saving": False,
		}
		save_json(settings, get_path(["settings.json"]))

	if not os.path.isfile(get_path(add=["download", "blank.png"])):
		r = requests.get("https://raw.githubusercontent.com/vdstendarr/vdstendarr/main/blank.png")
		with open(get_path(add=["download", "blank.png"]),"wb") as f:
			f.write(r.content)

	return st_folders


def generate_avatar(user_id):
	pass


def get_user_info(user_id):
    r = requests.get(f"https://habitica.com/api/v3/members/{user_id}", headers=headers)
    response = r.json()
    print(response["success"])
    return response


def get_group_members(group_id, number_of_members):
    params = {
        "limit": number_of_members,
        'includeAllPublicFields': 'true',
    }
    r = requests.get(f'https://habitica.com/api/v3/groups/{group_id}/members', params=params, headers=headers)
    response = r.json()
    print(response["success"])
    return response


def test_login(USER_ID, API_TOKEN):
	headers = {
		"x-api-user": USER_ID, 
		"x-api-key": API_TOKEN, 
		"x-client": f"{USER_ID}-CapiAvatarDownloader"
	}
	r = requests.get(f"https://habitica.com/api/v3/user/anonymized", headers=headers)
	return r.status_code


def parse_user_info(user_data):
	slots = ["back", "armor", "body", "head", "eyewear", "headAccessory", "weapon", "shield"]
	features = ["hair", "size", "skin", "shirt", "chair"]
	user = {}

	user["id"] = user_data["_id"]
	user["username"] = user_data["auth"]["local"]["username"]
	user["pet"] = user_data["items"]["currentPet"] if "currentPet" in user_data["items"].keys() else ""
	user["mount"] = user_data["items"]["currentMount"] if "currentMount" in user_data["items"].keys() else ""
	user["allow_costume"] = user_data["preferences"]["costume"] if "costume" in user_data["preferences"].keys() else False
	user["background"] = user_data["preferences"]["background"]
	user["appearance"] = {}
	user["gear"] = {}
	user["costume"] = {}

	for feature in features:
		user["appearance"][feature] = user_data["preferences"][feature]

	for slot in slots:
		equipped = user_data["items"]["gear"]["equipped"]
		costume = user_data["items"]["gear"]["costume"]
		eq = equipped[slot] if slot in equipped.keys() else ""
		cs = costume[slot] if slot in costume.keys() else ""
		user["gear"][slot] = eq
		user["costume"][slot] = cs
		
	return user


def download_image(img_id, extension, temp=True):
	link_base = "https://habitica-assets.s3.amazonaws.com/mobileApp/images/"
	LINK = f"{link_base}{img_id}.{extension}"
	path_base = temp_path if temp else download_path
	file_path = f"{path_base}/{img_id}.{extension}"
	if not os.path.isfile(file_path):
		r = requests.get(LINK)
		with open(file_path,"wb") as f:
			f.write(r.content)
		return r
	#urllib.request.urlretrieve(LINK, download_path)


def download_user_images(user):
	character = {
		"background": "",
		"pet": "",
		"skin": "",
		"base": "",
		"bangs": "",
		"beard": "",
		"mustache": "",
		"flower": "",
		"shirt": ""
	}
	gear = {
		"head": "",
		"armor": "",
		"shield": "",
		"eyewear": "",
		"weapon": "",
		"body": "",
		"back": "",
		"headAccessory": ""
	}
	costume = {
		"head": "",
		"armor": "",
		"shield": "",
		"eyewear": "",
		"weapon": "",
		"body": "",
		"back": "",
		"headAccessory": ""
	}

	if user["pet"] != "":
		character["pet"] = f"Pet-{user['pet']}"
	if user["mount"] != "":
		character["mount_head"] = f"Mount_Head_{user['mount']}"
		character["mount_body"] = f"Mount_Body_{user['mount']}"
	if user["background"] != "":
		character["background"] = f"background_{user['background']}"

	sleepy = ""
	if SETTINGS["is_sleepy"]:
		sleepy = "_sleep"

	character["skin"] = f"skin_{user['appearance']['skin']}{sleepy}"
	character["base"] = f"hair_base_{user['appearance']['hair']['base']}_{user['appearance']['hair']['color']}"
	character["bangs"] = f"hair_bangs_{user['appearance']['hair']['bangs']}_{user['appearance']['hair']['color']}"
	character["beard"] = f"hair_beard_{user['appearance']['hair']['beard']}_{user['appearance']['hair']['color']}"
	character["mustache"] = f"hair_mustache_{user['appearance']['hair']['mustache']}_{user['appearance']['hair']['color']}"
	character["flower"] = f"hair_flower_{user['appearance']['hair']['flower']}"
	character["shirt"] = f"{user['appearance']['size']}_shirt_{user['appearance']['shirt']}"

	for equip_slot in ["back", "armor", "body", "head", "headAccessory", "eyewear", "weapon", "shield"]:
		if equip_slot == "armor":
			gear[equip_slot] = f"{user['appearance']['size']}_{user['gear'][equip_slot]}"
		else:
			gear[equip_slot] = f"{user['gear'][equip_slot]}"

	for equip_slot in ["back", "armor", "body", "head", "headAccessory", "eyewear", "weapon", "shield"]:
		if equip_slot == "armor":
			costume[equip_slot] = f"{user['appearance']['size']}_{user['costume'][equip_slot]}"
		else:
			costume[equip_slot] = f"{user['costume'][equip_slot]}"


	checks1 = ['_base_0', '_none']
	checks2 = ['hair_', '_0']
	downloadable = []

	downloadable.append("zzz")
	downloadable.append("head_0")

	for k, v in character.items():
		if v != "":
			downloadable.append(v)

	for k, v in gear.items():
		if v != "":
			downloadable.append(v)

	for k, v in costume.items():
		if v != "":
			downloadable.append(v)

	for img_id in downloadable:
		if any(x in img_id for x in checks1):
			continue
		if all(x in img_id for x in checks2):
			continue
		else:
			response = download_image(img_id, "png", temp_saving)
			if response != None:
				if response.status_code != 200:
					tries_list = [
						(f"{img_id}", "gif"),
						(f"shop_{img_id}", "gif"),
						(f"shop_{img_id}", "png")
					]
					for t in tries_list:
						print(t)
						response = download_image(t[0], t[1], temp_saving)
						if response.status_code == 200:
							break
	
	return character, gear, costume


def assemble_avatar(user, downloaded):
	W, H = (141, 147)
	character, gear, costume = downloaded
	images_path = temp_path if temp_saving else download_path
	image = {
		"background": "",  # char
		"pet": "",
		"mount_head": "",
		"mount_body": "",
		"skin": "",
		"base": "",
		"bangs": "",
		"beard": "",
		"mustache": "",
		"flower": "",
		"shirt": "",
		"head": "",  # gear
		"armor": "",
		"shield": "",
		"eyewear": "",
		"weapon": "",
		"body": "",
		"back": "",
		"headAccessory": ""
	}

	for key, value in character.items():
		for extension in ["png", "gif"]:
			if os.path.isfile(f"{images_path}/{value}.{extension}"):
				image[key] = f"{images_path}/{value}.{extension}"

	equipped = costume if user["allow_costume"] and SETTINGS["allow_costume"] else gear

	for key, value in equipped.items():
		for extension in ["png", "gif"]:
			if os.path.isfile(f"{images_path}/{value}.{extension}"):
				image[key] = f"{images_path}/{value}.{extension}"

	buggy = [
		f"{images_path}/shield_special_spring2022Warrior.png",
		f"{images_path}/shield_armoire_masteredShadow.png",
		f"{images_path}/weapon_armoire_shootingStarSpell.png"
	]
	# start constructing image
	is_mounted = 0 if image['mount_head'] == "" or allow_mount is False else 24
	blank = Image.new('RGBA', (W, H))
	image_editable = blank.copy()

	if image['background'] != "" and allow_background:
		image_editable.paste(Image.open(image['background']).convert("RGBA"))

	if image['mount_body'] != "" and allow_mount:
		mount_body_img = Image.open(image['mount_body']).convert("RGBA")
		image_editable.paste(mount_body_img, (24, 18), mount_body_img)
	
	if image['skin'] != "":
		skin_img = Image.open(image['skin']).convert("RGBA")
		image_editable.paste(skin_img, (24, 24 - is_mounted), skin_img)

	for hair_type in ['base', 'bangs', 'beard', 'mustache', 'flower']:
		if user['appearance']['hair'][hair_type] != 0:
			hair_img = Image.open(image[hair_type]).convert("RGBA")
			image_editable.paste(hair_img, (24, 24 - is_mounted), hair_img)

	if user['appearance']['shirt'] != "":
		shirt_img = Image.open(image['shirt']).convert("RGBA")
		image_editable.paste(shirt_img, (24, 24 - is_mounted), shirt_img)

	head_contour_img = Image.open(f"{images_path}/head_0.png").convert("RGBA")
	image_editable.paste(head_contour_img, (24, 24 - is_mounted), head_contour_img)

	for equip_slot in ['back', 'armor', 'body', 'head', 'headAccessory', 'eyewear', 'weapon', 'shield']:
		if image[equip_slot] == "":
			continue
		if equip_slot in ['weapon', 'shield'] and not allow_weapons:
			continue 
		if image[equip_slot] in buggy and not allow_buggy:
			continue

		slot_img = Image.open(image[equip_slot])
		image_editable.paste(slot_img, (24, 24 - is_mounted), slot_img.convert("RGBA"))

	if user['mount'] != "" and allow_mount:
		mount_head_img = Image.open(image['mount_head']).convert("RGBA")
		image_editable.paste(mount_head_img, (24, 18), mount_head_img)

	if user['pet'] != "" and allow_pet:
		pet_img = Image.open(image['pet']).convert("RGBA")
		image_editable.paste(pet_img, (0, 48), pet_img)

	if SETTINGS["is_sleepy"]:
		sleepy_img = Image.open(f"{images_path}/zzz.png").convert("RGBA")
		image_editable.paste(sleepy_img, (24, 24 - is_mounted), sleepy_img)

	if allow_timestamp:
		timestamp = f"_{int(datetime.timestamp(datetime.now()))}"
	else:
		timestamp = ""

	filename = f'{user["id"]}{timestamp}.png'
	avatar_path = get_path(add=['avatar', filename])
	image_editable.save(avatar_path)
	return avatar_path


def erase_temp():	
	for file in os.listdir(temp_path):
		os.remove(os.path.join(temp_path, file))


def login_window():
	appname = 'AvatarDownloader'

	layout = [
		[gui.Text('User ID')],
		[gui.InputText(s=(34,1), k="_USER_ID")],
		[gui.Text('API Token')],
		[gui.InputText(s=(34,1), password_char="●",k="_API_TOKEN")],
		[gui.Checkbox("Remember me", k="_REMEMBER")],
		[gui.Button('Login', k="-LOGIN-")]
	]

	window = gui.Window(
		appname,
		layout,
		element_justification="center"
	)
	return window


def main_window():
	appname = 'AvatarDownloader'

	image_column = [
		[gui.Image(source=get_path(['download', 'blank.png']), k="_IMAGE_DISPLAY")]
	]

	l_c = [
		[gui.Checkbox("Costume", default=SETTINGS['allow_costume'], k="allow_costume")],
		[gui.Checkbox("Background", default=SETTINGS['allow_background'], k="allow_background")],
		[gui.Checkbox("Sleeping", default=SETTINGS['is_sleepy'], k="is_sleepy")]
	]

	c_c = [
		[gui.Checkbox("Mount", default=SETTINGS['allow_mount'], k="allow_mount")],
		[gui.Checkbox("Pet", default=SETTINGS['allow_pet'], k="allow_pet")],
		[gui.Checkbox("Weapons", default=SETTINGS['allow_weapons'], k="allow_weapons")]
	]

	r_c = [
		[gui.Checkbox("Buggy", default=SETTINGS['allow_buggy'], k="allow_buggy")],
		[gui.Checkbox("Timestamp", default=SETTINGS['allow_timestamp'], k="allow_timestamp")],
		[gui.Checkbox("Temp saving", default=SETTINGS['temp_saving'], k="temp_saving")]
	]

	options_column = [
		[gui.Text('Target User ID')],
		[gui.InputText(s=(42,1), justification="c", k="_TARGET_ID")],
		[gui.Text("", text_color = "red", k="_ERROR")],
		[gui.Column(l_c), gui.Column(c_c), gui.Column(r_c)],
		[gui.Button('Download', k="-DOWNLOAD-"), gui.Button('Group (Not tested)', disabled=True, k="-GROUP_DOWNLOAD-")]
	]

	layout = [
		[gui.Column(image_column), gui.Column(options_column, element_justification="c")]
	]

	window = gui.Window(
		appname,
		layout
	)
	return window


def download_one(user_id, wait=False):
	if wait:
		time.sleep(2)
	try:
		a = get_user_info(user_id)
		b = parse_user_info(a["data"])
		avatar_path = assemble_avatar(b, download_user_images(b))
		erase_temp()
		return avatar_path, b
	except Exception as e:
		return f"{e}"

# Switches and settings
avatar_path, download_path, temp_path = populate_folders()

SETTINGS = open_json(get_path(["settings.json"]))

allow_mount = SETTINGS["allow_mount"]
allow_pet = SETTINGS["allow_pet"]
allow_background = SETTINGS["allow_background"]
allow_weapons = SETTINGS["allow_weapons"]
allow_buggy = SETTINGS["allow_buggy"]
allow_timestamp = SETTINGS["allow_timestamp"]
is_sleepy = SETTINGS["is_sleepy"]
temp_saving = SETTINGS["temp_saving"]

headers = {
	"x-api-user": SETTINGS["USER_ID"], 
	"x-api-key": SETTINGS["API_TOKEN"], 
	"x-client": f"{SETTINGS['USER_ID']}-CapiAvatarDownloader"
}

#main()
gui.theme('Reddit')

if SETTINGS["USER_ID"] == "" or SETTINGS["API_TOKEN"] == "":
	print("###")
	window = login_window()
else:
	window = main_window()
	
_remember = None

group_download_count = 0

while True:
	event, values = window.read()

	if event != '__TIMEOUT__':
		print(event, values)
		print()

	if event == gui.WIN_CLOSED:
		break

	if event == "-LOGIN-":
		SETTINGS["USER_ID"] = values["_USER_ID"]
		SETTINGS["API_TOKEN"] = values["_API_TOKEN"]
		test_result = test_login(SETTINGS["USER_ID"], SETTINGS["API_TOKEN"])
		
		if test_result == 200:
			headers = {
				"x-api-user": SETTINGS["USER_ID"], 
				"x-api-key": SETTINGS["API_TOKEN"], 
				"x-client": f"{SETTINGS['USER_ID']}-CapiAvatarDownloader"
			}
			if values["_REMEMBER"]:
				_remember = True
				save_json(SETTINGS, get_path(["settings.json"]))
			window.close()
			window = main_window()

	if event in ["-DOWNLOAD-", "-GROUP_DOWNLOAD-"]:
		SETTINGS2 = {}
		SETTINGS2["USER_ID"] = SETTINGS["USER_ID"]
		SETTINGS2["API_TOKEN"] = SETTINGS["API_TOKEN"]
		if _remember == False:
			SETTINGS2["USER_ID"] = ""
			SETTINGS2["API_TOKEN"] = ""
		SETTINGS2["allow_mount"] = values["allow_mount"]
		SETTINGS2["allow_pet"] = values["allow_pet"]
		SETTINGS2["allow_background"] = values["allow_background"]
		SETTINGS2["allow_costume"] = values["allow_costume"]
		SETTINGS2["allow_weapons"] = values["allow_weapons"]
		SETTINGS2["allow_buggy"] = values["allow_buggy"]
		SETTINGS2["allow_timestamp"] = values["allow_timestamp"]
		SETTINGS2["is_sleepy"] = values["is_sleepy"]
		SETTINGS2["temp_saving"] = values["temp_saving"]
		save_json(SETTINGS2, get_path(["settings.json"]))
		for k in SETTINGS.keys():
			if k not in ["USER_ID", "API_TOKEN"]:
				SETTINGS[k] = SETTINGS2[k]
		allow_mount = SETTINGS["allow_mount"]
		allow_pet = SETTINGS["allow_pet"]
		allow_background = SETTINGS["allow_background"]
		allow_weapons = SETTINGS["allow_weapons"]
		allow_buggy = SETTINGS["allow_buggy"]
		allow_timestamp = SETTINGS["allow_timestamp"]
		is_sleepy = SETTINGS["is_sleepy"]
		temp_saving = SETTINGS["temp_saving"]

	if event == "-DOWNLOAD-":
		window["-DOWNLOAD-"].update(disabled=True)
		#window["-GROUP_DOWNLOAD-"].update(disabled=True)
		window.perform_long_operation(lambda : download_one(values["_TARGET_ID"], wait=False), '-END_DOWNLOAD-')

	if event == "-GROUP_DOWNLOAD-":
		window["-DOWNLOAD-"].update(disabled=True)
		#window["-GROUP_DOWNLOAD-"].update(disabled=True)
		user_info = get_user_info(SETTINGS["USER_ID"])
		group = get_group_members(user_info["data"]["party"]["_id"], 30)
		group_len = len(group["data"])
		group_download_count = 0
		for entry in group["data"]:
			uid = entry["_id"]
			#image_show_path = download_one(uid)
			window.perform_long_operation(lambda : download_one(uid, wait=True), '-END_DOWNLOAD_GROUP-')
			#print(image_show_path)
		group_finished = True

	if event == "-END_DOWNLOAD-":
		window["-DOWNLOAD-"].update(disabled=False)
		#window["-GROUP_DOWNLOAD-"].update(disabled=False)
		if type(values["-END_DOWNLOAD-"]) is str:
			window["_ERROR"].update(text_color="red")
			window["_ERROR"].update("Invalid ID")
			window["_IMAGE_DISPLAY"].update(source=get_path(['download', 'blank.png']))
			window["_IMAGE_DISPLAY"].set_tooltip("")
		else:
			window["_ERROR"].update(text_color="green")
			window["_ERROR"].update(values["-END_DOWNLOAD-"][1]["username"])
			window["_IMAGE_DISPLAY"].update(source=values["-END_DOWNLOAD-"][0])
			window["_IMAGE_DISPLAY"].set_tooltip(values["-END_DOWNLOAD-"][1]["username"])
		window.refresh()

	if event == "-END_DOWNLOAD_GROUP-":
		group_download_count += 1
		#print(group_download_count, group_len)
		if group_download_count == group_len:
			window["-DOWNLOAD-"].update(disabled=False)
			window["-GROUP_DOWNLOAD-"].update(disabled=False)
		if type(values["-END_DOWNLOAD_GROUP-"]) is str:
			window["_ERROR"].update(text_color="red")
			window["_ERROR"].update(f"Invalid ID ({group_download_count}/{group_len})")
		else:
			window["_ERROR"].update(text_color="green")
			window["_ERROR"].update(f"{values['-END_DOWNLOAD_GROUP-'][1]['username']} ({group_download_count}/{group_len})")
			window["_IMAGE_DISPLAY"].update(source=values["-END_DOWNLOAD_GROUP-"][0])
			window["_IMAGE_DISPLAY"].set_tooltip(values["-END_DOWNLOAD_GROUP-"][1]["username"])
		window.refresh()

			
	window.refresh()

window.close()