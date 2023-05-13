import sys, os, requests, json, shutil
from urllib.parse import quote_plus as enc
from colors import Colors


def main(argv):
    global js_defs, confLen
    files = []
    confDir = False
    with open('config.json') as f_defs:
        js_defs = json.load(f_defs)
    with open('modlist.json') as f_mods:
        js_mods = json.load(f_mods)
    mUrl = js_defs['modrinth_url']
    for id in js_mods['modrinth']:
        ver = modrinth(mUrl, id)
        files += getFiles(ver)
    print(f"{Colors.BLUE}Versions selected, Saving output...{Colors.END}")
    if not os.path.exists("./output/"):
        os.mkdir("./output/")
    saveOutput(files)
    if 'copy_from' in js_defs and js_defs['copy_from'] != False:
        confDir = os.path.expanduser(js_defs['copy_from'])
    if(confDir):
        if(os.path.exists("./output/overrides/")):
            shutil.rmtree("./output/overrides/")
        confLen = len(confDir)
        shutil.copytree(confDir, "./output/overrides/", ignore=ignoreFunc)
        print(f"{Colors.LIGHT_CYAN}Copied Config/Cache Files to Output.{Colors.END}")
    if os.path.exists(js_defs['curseforge_dir']):
        shutil.copytree(js_defs['curseforge_dir'], "./output/overrides/mods/")
        print(f"{Colors.LIGHT_CYAN}Copied Curseforge Mods to Output.{Colors.END}")
    shutil.make_archive(f"./{js_defs['output']}", 'zip', "./output/")
    print(f"{Colors.LIGHT_CYAN}Zipped Output.{Colors.END}")
    if os.path.exists(f"{js_defs['output']}.mrpack"):
        os.remove(f"{js_defs['output']}.mrpack")
    os.rename(f"{js_defs['output']}.zip", f"{js_defs['output']}.mrpack")
    print(f"{Colors.LIGHT_GREEN}Successfully Saved mrPack Output.{Colors.END}")
    
def ignoreFunc(src, names):
    if src[confLen:] == '':
        return [name for name in names if name not in (js_defs['include_files'] + js_defs['include_subdirs'])]
    subdir = src[confLen+1:]
    if os.sep in subdir:
        subdir = subdir[:subdir.index(os.sep)]
    if subdir in js_defs['include_subdirs']:
        return []
    return names

def getLoaderVer():
    rsp = requests.get(js_defs['loader_url'])
    if(rsp.status_code != 200):
        print(f"{Colors.RED}Error Status Code: {rsp.status_code} getting Loader Version{Colors.END}")
        return ""
    rspJson = rsp.json()
    filt = [ver for ver in rspJson if ver['stable']]
    return filt[0]['version']

def saveOutput(files):
    out = {}
    out['formatVersion'] = js_defs['formatVersion']
    out['game'] = js_defs['game']
    out['versionId'] = js_defs['versionId']
    out['name'] = js_defs['name']
    out['summary'] = js_defs['summary']
    out['dependencies'] = {
        'minecraft': js_defs['versions'][0],
        js_defs['loader_depend']: getLoaderVer()
    }
    out['files'] = files
    with open('output/modrinth.index.json', 'w', encoding="UTF-8") as f_out:
        json.dump(out, f_out, indent=4)
    print(f"{Colors.LIGHT_CYAN}Saved Metadata Output.{Colors.END}")

def modrinth(url, id):
    rsp = requests.get(url + "project/" + id)
    if(rsp.status_code != 200):
        print(f"{Colors.RED}Error getting info for project {id}, code: {rsp.status_code}")
        return None
    acxm = js_defs['autoconfirm-exact-match']
    acbm = js_defs['autoconfirm-beta-match']
    rspInf = rsp.json()
    modStr(rspInf)
    loaders = '"' + '","'.join(js_defs['loaders']) + '"'
    versions = '"' + '","'.join(js_defs['versions']) + '"'
    rsp = requests.get(url + f"project/{id}/version?loaders=[{loaders}]&game_versions=[{versions}]")
    if(rsp.status_code != 200):
        print(f"{Colors.RED}Error getting versions for project {id}, code: {rsp.status_code}")
        return None
    rspVer = rsp.json()
    if(len(rspVer) == 0):
        print(f"{Colors.LIGHT_RED}No Versions Available from given version list.{Colors.END}")
        return None
    filter = [ver for ver in rspVer if js_defs['versions'][0] in ver['game_versions']]
    if(len(filter) == 0):
        print(f"{Colors.LIGHT_RED}No Primary Version Available, listing all Related Versions{Colors.END}")
        acxm = False # the below alg doesnt expect the unfiltered list, so require confirming everything
        acbm = False
        filter = [ver for ver in rspVer]
    if(len(filter) == 1):
        print(f"{Colors.PURPLE}Found Exact Version:{Colors.END}")
        verStr(filter[0])
        if acxm or input("Confirm this Version (Y/N): ").lower() == 'y':
            return filter[0]
    filter = sorted(filter, key = lambda x:x['date_published'], reverse=True)
    if(filter[0]['featured'] or filter[0]['version_type'] == "release"):
        print(f"{Colors.PURPLE}Found Featured Update:{Colors.END}")
        verStr(filter[0])
        if acxm or input("Confirm this Version (Y/N): ").lower() == 'y':
            return filter[0]
    if not any(ver['featured'] or ver['version_type']=="release" for ver in filter):
        print(f"{Colors.BROWN}Found Updated Beta:{Colors.END}")
        verStr(filter[0])
        if acbm or input(f"Confirm this {Colors.YELLOW}Beta{Colors.END} Version (Y/N): ").lower() == 'y':
            return filter[0]
    print(f"{Colors.YELLOW}No Best Match Found, Select one below:{Colors.END}")
    for i in range(len(filter)):
        verStrN(filter[i], i+1)
    selN = int(input(f"{Colors.PURPLE}Enter Selection # or 0 to skip mod:{Colors.END} "))
    if(selN > 0 and selN <= len(filter)):
        return filter[selN-1]
    return None

def getFiles(ver):
    if not ver: return []
    vf = [x for x in ver['files'] if x['primary']]
    if(len(vf) == 0): 
        print(f"{Colors.RED}No Primary Files found for project {Colors.CYAN}{ver['project_id']}{Colors.END}")
        return []
    vout = []
    for file in vf:
        vout.append({
            'path': 'mods/' + file['filename'],
            'downloads': [file['url']],
            'hashes': file['hashes'],
            'fileSize': file['size']
        })
    return vout
    

def modStr(mod):
    print(f"{Colors.GREEN}{mod['title']}{Colors.DARK_GRAY} - ({mod['slug']} - {mod['id']}){Colors.END}")
    
def verStr(ver):
    ft = ""
    if(ver['featured']):
        ft = f"{Colors.RED} featured{Colors.END}"
    print(f"{ft} {ver['version_type']} {Colors.CYAN}{ver['version_number']}{Colors.END} for MC Versions: {Colors.BLUE}{str(ver['game_versions'])}{Colors.BROWN} ({str(ver['loaders'])}){Colors.DARK_GRAY} {ver['name']}{Colors.END}")

def verStrN(ver, i):
    ft = ""
    if(ver['featured']):
        ft = f"{Colors.BLUE}featured"
    print(f"{Colors.RED}{i}: {ft}{Colors.END} {ver['version_type']} {Colors.CYAN}{ver['version_number']}{Colors.END} for MC Versions: {Colors.BLUE}{str(ver['game_versions'])}{Colors.BROWN} ({str(ver['loaders'])}){Colors.DARK_GRAY} {ver['name']}{Colors.END}")


if __name__ == "__main__":
   main(sys.argv[1:])