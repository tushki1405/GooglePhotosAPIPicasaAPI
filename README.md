# GooglePhotosAPIPicasaAPI
Using Google photos API (Picasa API) to upload pictures from desktop to Google photos. Script can do the following:
- Show all existing albums
- Dry Run mode - will show what the script will do, but won't upload pics
- Uploads all images

## Steps
- Download library gdata-python-client
- Add PYTHONPATH with path where the library is extracted [Steps here](https://developers.google.com/gdata/articles/python_client_lib)
- Create keys in google cloud project and get ID and Secret Key [Steps here](https://developers.google.com/identity/protocols/OAuth2)
- Install all dependencies. All packages on my system are in packages.txt
- Open UploadPhotos.py and change config variables (Set MODE=1/2 initially)
- If everything looks good then run the script with MODE=3
