from shakespeare_scripts import ShakespeareDB, ScriptTex
import yaml

# Choose play by WorkID in OSS DB
WorkID = 'comedyerrors'

# Load roles config file for play
with open('./configs/'+WorkID+'.yaml') as file:
    doc = yaml.load(file, Loader=yaml.FullLoader)
    players = doc['players']

db = ShakespeareDB()

# Generate Script for each player
for player in players:

    script = ScriptTex('./scripts/', WorkID+'_'+player+'.tex')

    # Front Matter
    script.add_preamble(title=db.get_title(WorkID),
                        author='William Shakespeare')

    script.add_characters(db.get_characters(WorkID))

    scenes = db.get_scene_numbers(WorkID)
    last_act = -1

    # Body
    for scene in scenes:
        current_act = int(scene['Section'])
        if current_act > last_act:
            last_act = current_act
            script.add_act()
        script.add_scene(scene['Description'])
        lines = db.get_scene(WorkID, scene['Section'], scene['Chapter'])

        script.add_lines(lines, players[player])

    script.end()
    script.make_pdf()
