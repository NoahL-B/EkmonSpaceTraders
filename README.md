# EkmonSpaceTraders

## Before you begin:

Use requirements.txt to ensure you have all the packages you need.

The SpacePyTraders package is designed for SpaceTraders API V1, and this repository was built for SpaceTraders API V2.
In order to make this application work, the following change has to be made:

in SpacePyTraders\client.py the function make_request(method, url, headers, params) should be changed to the following:

    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, json=params)
    elif method == "PUT": 
        return requests.put(url, headers=headers, data=params)
    elif method == "DELETE":
        return requests.delete(url, headers=headers, params=params)
    elif method == "PATCH":
        return requests.patch(url, headers=headers, data=params)

    # If an Invalid method provided throw exception
    if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
        logging.exception(f'Invalid method provided: {method}')


If I knew how to do this through git, I would. Unfortunately, I don't, so you'll have to handle it on your own.


## Usage:

This repository stores information in a Microsoft Access database. I'm not including it in the git distribution because 
it stores my tokens and weekly data. Make a copy of SpaceTradersDatabase-SAMPLE.accdb and rename it to 
SpaceTradersDatabase.accbd, then add your username and token to the ID column.

After each reset, old data is saved to a folder called old_data. Make this folder before you run Reset_Procedure.py.
Also set your username and faction on lines 11 and 12 of Reset_Procedure.py.

As it currently stands, main won't run with just the two starter ships. Either remove the surveyor from the command
ship, or buy and equip a ship with only mining laser(s) to run the script. Then Main should take care of the rest.


## Known Issues:

Occasionally the code will exit with exit code (0xC0000005) or (0xC0000374). I have no idea why this happens, but I'm 
looking into it.