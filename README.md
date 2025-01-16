# EkmonSpaceTraders

## About:

This is a client for the SpaceTraders API game. Documentation for the game can be found at https://spacetraders.io/ 

## Before you begin:

Use requirements.txt to ensure you have all the packages you need.

Create a folder called old_data in the project root folder.

Make a copy of SpaceTradersDatabase-SAMPLE.accdb and rename it to SpaceTradersDatabase.accdb. Add your username and token to the ID table of the database.


## Usage:

This repository stores information in a Microsoft Access database. I'm not including it in the git distribution because 
it stores my tokens and weekly data. You can provide an existing token (or tokens) to the ID table. You can create new agents by running Reset_Procedure.py, making sure to modify it first to reflect your desired username and faction.

After each reset, old data is saved to the old_data folder. Make this folder before you run Reset_Procedure.py.
Also set your username and email on lines 4 and 5 of __SECRETS.py.

After creating or adding your agent info, run Startup_Procedure.py to add information about every system and waypoint to the database. The startup procedure will also start making profitable trades with your command ship!

Once the startup procedure has completed, you can run main.py. Be sure to watch the console output, as sometimes it will inform you that the program needs to restart for the sake of running newly-purchased ships!

## Known Issues:

Occasionally the code will exit with exit code (0xC0000005) or (0xC0000374). I have no idea why this happens, but I'm 
looking into it.