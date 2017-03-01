# GooglePhotosApi(PicasaAPI)
Using Google photos API (Picasa API) to upload pictures from desktop to Google photos. Script can do the following:
- Show all existing albums
- Dry Run mode - will show what the script will do, but won't upload pics
- Uploads all images

## Steps
- Download library `gdata-python-client`
- Add `PYTHONPATH` with path where the library is extracted [Steps here](https://developers.google.com/gdata/articles/python_client_lib)
- Create keys in google cloud project and get ID and Secret Key [Steps here](https://developers.google.com/identity/protocols/OAuth2)
- Install all dependencies. All packages on my system are in `packages.txt`
- Create a new album for uploading photos on Google Photos.
- Open `UploadPhotos.py` and change config variables (Set `MODE=1` initially)
- Run the script and install all missing dependencies/resolve python errors. You should see list of all you albums including the one you created.
- Copy the id of that album (numeric number) and add it to config.
- Run the script with `MODE=2`. You should see all messages of what the script will do.
- If everything looks good, then run with `MODE=3`. You should see all photos that have been uploaded.

## Things to note
- if `client_secrets.json` and `credentials.dat` are not created automatically, then create blank files manually.
- `result.log` file contains all log messages that are also displayed on the console.
- `error.log` file contains path of all images that may not have been uploaded
- `other_files.log` contains path of all files that were not image files found in the folders.
- Script adds all pictures recursively while doing the following:
  - Say your picture is in `rootdir/Trip1/Beach/pic1.jpg`. Then the file name would be `pic1.jpg` and summary of pic would be `Trip1, Beach`
  - If the folder (not root folder) has date (e.g. `2017-02-28 - Beach day`), then you can set `UPDATE_FILE_METADATA` in config to `True`. This will check all pics in that folder and update metadata date to `2017-02-28` if date on picture and folder differs by more than `FILE_METADATA_DATE_TOLERANCE` (in config)
  
