import sys, requests, json, os
from urllib.parse import quote_plus as enc
from colors import Colors

output = []

def main(argv):
    method = 'modrinth'
    srch = []
    with open('config.json') as f_defs:
        js_defs = json.load(f_defs)
    if(len(argv) > 0):
        with open(argv[0], 'r') as f_srch:
            srchjs = json.load(f_srch)
            srch = srchjs[method]
    if(len(argv) > 1 and argv[1] == 'curseforge'):
        method = 'curseforge'
    if(method == 'modrinth'):
        modrinth(srch, js_defs)
    print(f"{Colors.LIGHT_PURPLE}Finished Selecting Mods:{Colors.END}")
    for i in range(0, len(output)):
        print(f"{Colors.BLUE}{output[i][1]}{Colors.DARK_GRAY} - {output[i][0]}{Colors.END}")
    if(len(output) == 0):
        print(f"{Colors.RED}No mods selected, cancelling.{Colors.END}")
    else:
        if(os.path.exists('modlist.json')): 
            # only replaces the relevant method (so if modlist contains modrinth and curseforge ids, it won't replace curseforge when writing modrinth)
            # IT STILL REPLACES ALL EXISTING MODS in the list thats being updated. Don't be fooled by the r+ file mode.
            with open('modlist.json', 'r+') as f_mods:
                outjs = json.load(f_mods)
                out = list(zip(*output))
                outjs[method] = out[0]
                outjs[method + '_slug'] = out[2]
                f_mods.truncate(0)
                f_mods.seek(0)
                json.dump(outjs, f_mods, indent=4)
            print(f"{Colors.LIGHT_GREEN}Saved updated modlist file.{Colors.END}")
        else:
            with open('modlist.json', 'w') as f_mods:
                outjs = {}
                out = list(zip(*output))
                outjs[method] = out[0]
                outjs[method + '_slug'] = out[2]
                json.dump(outjs, f_mods, indent=4)
            print(f"{Colors.LIGHT_GREEN}Saved new modlist file.{Colors.END}")

def modrinth(srch, js_defs):
    vers = js_defs['versions']
    url = js_defs['modrinth_url']
    acxm = ("autoconfirm-exact-match" in js_defs and js_defs["autoconfirm-exact-match"])
    url_srch = url + 'search?facets=[["project_type:mod"]]&query='
    srch.append('exit')
    sIter = iter(srch)
    loopQuery(url_srch, vers, True, lambda : next(sIter))
    loopQuery(url_srch, vers, acxm, lambda : input(f"{Colors.LIGHT_GRAY}Enter next mod search (or type 'exit'): {Colors.END}"))

def loopQuery(url_srch, vers, acxm, func):
    query = func()
    if(query != "exit"):
        rsp = requests.get(url_srch + enc(query))
        if(rsp.status_code != 200):
            print("Error code: " + rsp.status_code)
            loopQuery(url_srch, vers, acxm, func)
            return
        srch = rsp.json()
        if(srch['total_hits'] == 0):
            print(f"{Colors.YELLOW}Couldn't find anything like that.{Colors.END}")
            loopQuery(url_srch, vers, acxm, func)
            return
        found = None
        for hit in srch['hits']:
            if(hit['slug'] == query or hit['title'] == query):
                print('Exact match: ' + strxhit(hit))
                confx = 'y'
                if not any(ver in vers for ver in hit['versions']):
                    print(f"{Colors.YELLOW}NOTE: No Matching Versions:{Colors.END} {str(hit['versions'])}")
                    confx = input(f"Confirm this option anyway? {Colors.YELLOW}(Y/N){Colors.END}:")
                elif not acxm:
                    confx = input(f"Confirm this option? {Colors.YELLOW}(Y/N){Colors.END}:")
                elif hit['project_id'] in output:
                    print(f"{Colors.YELLOW}Skipping exact match, already added.{Colors.END}")
                    confx = 'n'
                if(confx.lower() == 'y'):
                    found = (hit['project_id'], hit['title'], hit['slug'])
                    print(f"Confirmed, added mod: {Colors.GREEN}{hit['title']}{Colors.END}")
                    break
                else:
                    print(f"{Colors.LIGHT_GRAY}Continuing search...{Colors.END}")
        if(found):
            output.append(found)
        else:
            print(f"{Colors.LIGHT_GRAY}No Exact Matches... Select an Option Below (or 0 to skip){Colors.END}")
            ind = 0
            for hit in srch['hits']:
                ind+=1
                print(f"{Colors.RED}{str(ind)}{Colors.END}: {strhit(hit)}")
            num = int(input('Mod Number: '))
            if(num > 0 and num <= ind):
                hit = srch['hits'][num-1]
                print('Selected: ' + strxhit(hit))
                output.append((hit['project_id'], hit['title'], hit['slug']))
            else:
                print(f"{Colors.LIGHT_GRAY}Skipping this search...{Colors.END}") 
        loopQuery(url_srch, vers, acxm, func)

def strxhit(hit):
    return f"{Colors.GREEN}{hit['title']}{Colors.END} by {Colors.CYAN}{hit['author']}{Colors.END} ({hit['slug']} - {hit['project_id']} - {hit['project_type']})"

def strhit(hit):
    return f"{strxhit(hit)}\n   Description: {Colors.BLUE}{hit['description']}{Colors.END}"

if __name__ == "__main__":
   main(sys.argv[1:])