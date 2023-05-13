# ModlistAutoUpdater
Updates all modrinth mods by major versions (semi-)automatically, and outputs a Modrinth Modpack (.mrpack) zipfile to import into your launcher.
Currently does not support Curseforge API because Curseforge has removed their public API. 
Modrinth is the only supported API-based mod fetcher. You can manually download your curseforge mods and put them in a folder named "curseforge" before running the program.

## Usage
Requires Python 3.7.
There are two configuration files: `config.json` and `searchlist.json`, and two python scripts: `modlister.py` and `mrpackgen.py`

#### SearchList.json
(Optional) This is the list of mod names to search for automatically on modrinth. Only used for the `modlister.py` script.
#### Modlister.py
This script generates a `modlist.json` file with the actual modrinth IDs for each mod. By default it will prompt for you to enter search terms interactively,
but it can be supplied with a search list in order to run automatically. If it finds multiple matches for a specific search, it will prompt for you to select which one by number.
When supplied with a searchlist, it will not prompt for additional searches and complete the modlist immediately. Because the modlist is overwriten every time this is run, there is an option `-a` to put on the end of the command line to let you add additional mods interactively.
```
python modlister.py <searchlist.json> [-a]
```
#### Config.json
This contains the main configuration for both `modlister.py` and `mrpackgen.py`.
(TODO add documentation for this)
#### mrpackGen.py
This is the main script to generate your modpack. It takes no commandline arguments, all settings are in `config.json`.
```
python mrpackgen.py
```
