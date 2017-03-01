'''
    # Copyright 2017, Tushar Gupta, All rights reserved.
    # You may use, distribute and modify this code under the terms of the
    ## GNU General Public License (https://www.gnu.org/licenses/gpl-3.0.en.html)
'''
import atom
import gdata.photos.service
import httplib2
import logging
import os,webbrowser
from datetime import datetime, timedelta
from gi.repository import GExiv2
from libxmp import XMPFiles, consts
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

####### Set these variables
#MODE = 1 - shows all albums
#MODE = 2 - shows log messages but does not actually upload images
#MODE = 3 - uploads all images
MODE = 3
# Directory where this script is and gdata-python-client is downloaded
# right now should be same directory
CONFIG_DIR = '/usr/local/google/home/'
# Root directory where all pictures are present.
PHOTO_DIR = '/usr/local/google/home/'
# Gmail address where pics have to up uploaded
EMAIL_ADDRESS = 'email@gmail.com'
# Username of gmail account
USERNAME = 'username'
# If folder name has a date(YYYY-MM-DD-FolderName), then if the below is True,
# the script checks if the difference in folder date and file date is more than
# UPDATE_FILE_METADATA. If yes, then file date is updated and set to folder date
UPDATE_FILE_METADATA = True
# If difference of file and folder date is greater than below value, then update
# file date
FILE_METADATA_DATE_TOLERANCE = 3
# album id where all pictures are to be uploaded
ALBUM_ID = 'albumId'

######## These can be changed but not required.
CLIENT_SECRET_FILE = 'client_secrets.json'
CREDENTIAL_STORE_FILE = 'credentials.dat'
LOG_FILE = 'result.log'
ERROR_LOG_FILE = 'error.log'
OTHER_LOG_FILE = 'other_files.log'
VERBOSE = True
# Namespaces that are checked to update file metadata.
# More consts can be added from here:
# https://github.com/python-xmp-toolkit/python-xmp-toolkit/blob/master/libxmp/consts.py
XMP_CONSTANTS = [consts.XMP_NS_RDF,
                 consts.XMP_NS_XMPMeta,
                 consts.XMP_NS_XMP_MM,
                 consts.XMP_NS_XMP_ResourceRef,
                 consts.XMP_NS_XMP,
                 consts.XMP_NS_Photoshop,
                 consts.XMP_NS_DC,
                 consts.XMP_NS_EXIF]
# These are the XMP properties that are updated. Script checks each property
# again every namespace defined in XMP_CONSTANTS
DATE_CONSTANTS = ['CreateDate', 'ModifyDate', 'DateCreated', 'DateTimeOriginal']

####### DO NOT CHANGE THESE
gd_client = None
DATE_FORMAT = '%Y:%m:%d %H:%M:%S'
DATE_FORMAT_XMP = '%Y:%m:%dT%H:%M:%S'
ERRORS = []
OTHER_FILES = []

def log(message, *args):
    logging.info(message, *args)
    if VERBOSE == True:
        print message % args

def myStr(obj):
    if obj is None or obj.text is None:
        return ''
    return obj.text

def RemoveFiles():
    if os.path.isfile(LOG_FILE):
        os.remove(LOG_FILE)
    if os.path.isfile(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)
    if os.path.isfile(OTHER_LOG_FILE):
        os.remove(OTHER_LOG_FILE)
    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

def WriteToFiles():
    if len(OTHER_FILES) > 0:
        f = open(OTHER_LOG_FILE, 'w')
        for file in OTHER_FILES:
            f.write(file + '\n')
        f.close()
    if len(ERRORS) > 0:
        f = open(ERROR_LOG_FILE, 'w')
        for file in ERRORS:
            f.write(file + '\n')
        f.close()

def getImageExtension(file):
    extension = os.path.splitext(file)[1]
    if extension == '.bmp':
        return 'bmp'
    elif extension == '.gif':
        return 'gif'
    elif extension == '.jpeg' or extension == '.jpg':
        return 'jpeg'
    elif extension == '.png':
        return 'png'
    return None

def isImageFile(file):
    return getImageExtension(file) is not None

def GetTimestampFromFolderName(folderName):
    folderName = folderName.replace(' ', '').strip()
    parts = folderName.split('-')
    if len(parts) < 4 or not parts[0].isdigit() \
        or not parts[1].isdigit() or not parts[2].isdigit():
        return None
    timestamp = int( \
        datetime(int(parts[0]), int(parts[1]), int(parts[2])).strftime('%s'))
    return str(timestamp * 1000)

def OAuth2Login(client_secrets, credential_store, email):
    scope = 'https://picasaweb.google.com/data/'
    agent = 'picasawebuploader'
    storage = Storage(credential_store)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(client_secrets,
                                       scope=scope,
                                       redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        uri = flow.step1_get_authorize_url()
        webbrowser.open(uri)
        code = raw_input('Enter the authentication code: ').strip()
        credentials = flow.step2_exchange(code)

    if (credentials.token_expiry - datetime.utcnow()) < timedelta(minutes=5):
        http = httplib2.Http()
        http = credentials.authorize(http)
        credentials.refresh(http)

    storage.put(credentials)

    return gdata.photos.service.PhotosService(source=agent,
                                              email=email,
                                              additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token})

def ShowAlbums():
    userFeed = gd_client.GetUserFeed(user=EMAIL_ADDRESS)
    for album in userFeed.entry:
        print '##################################'
        print 'Title: ' + album.title.text
        print 'Number of photos: ' + album.numphotos.text
        print 'Summary: ' + myStr(album.summary)
        print album.gphoto_id.text

def ShowPhotosInAlbum(albumId):
    url = '/data/feed/api/user/%s/albumid/%s?kind=photo' % (USERNAME, albumId)
    photos = gd_client.GetFeed(url)
    for photo in photos.entry:
        print 'Photo title:', photo.title.text
        print 'Tags:', photo.tags.text
        print 'Published:', photo.published.text
        print 'Summary:', myStr(photo.summary)

def GetDateFromExif(exif):
    if exif.has_tag('Exif.Photo.DateTimeDigitized'):
        return exif['Exif.Photo.DateTimeDigitized']
    elif exif.has_tag('Exif.Photo.DateTimeOriginal'):
        return exif['Exif.Photo.DateTimeOriginal']
    elif exif.has_tag('Exif.Image.DateTime'):
        return exif['Exif.Image.DateTime']
    elif exif.has_tag('Exif.Image.DateTimeOriginal'):
        return exif['Exif.Image.DateTimeOriginal']
    return None

def UpdateFileMetadata(filename, datetime):
    exif = GExiv2.Metadata(filename)
    if exif is not None:
        fileDate = GetDateFromExif(exif)
        if fileDate is not None:
            fileDate = datetime.strptime(fileDate, DATE_FORMAT)
            # date within acceptable limit. don't update
            if abs((fileDate - datetime).days) <= FILE_METADATA_DATE_TOLERANCE:
                return

    log('Updating exif: %s to date: %s', \
        filename, datetime.strftime(DATE_FORMAT))

    if DRY_RUN == False:
        if exif is not None:
            exif['Exif.Photo.DateTimeOriginal'] = datetime.strftime(DATE_FORMAT)
            exif['Exif.Photo.DateTimeDigitized'] = datetime.strftime(DATE_FORMAT)
            exif['Exif.Image.DateTime'] = datetime.strftime(DATE_FORMAT)
            exif['Exif.Image.DateTimeOriginal'] = datetime.strftime(DATE_FORMAT)
            exif.save_file()

        xmpfile = XMPFiles(file_path=filename, open_forupdate=True)
        xmp = xmpfile.get_xmp()
        if xmp is not None:
            for xmpConst in XMP_CONSTANTS:
                for dateConst in DATE_CONSTANTS:
                    if xmp.does_property_exist(xmpConst, dateConst):
                        xmp.set_property( \
                            xmpConst, dateConst, datetime.strftime(DATE_FORMAT_XMP))
            if (xmpfile.can_put_xmp(xmp)):
                xmpfile.put_xmp(xmp)
                xmpfile.close_file()

def AddPhoto(filename, summary, title, imageFormat='jpeg', timestamp=None):
    if isImageFile(filename) == False:
        log('Not Image: %s', filename)
        OTHER_FILES.append(filename)
        return
    log('Uploading photo: %s', filename)
    url = '/data/feed/api/user/%s/albumid/%s?kind=photo' % (USERNAME, ALBUM_ID)
    metadata = gdata.photos.PhotoEntry()
    metadata.title = atom.Title(text=title)
    metadata.summary = atom.Summary(text=summary, summary_type='text')
    if UPDATE_FILE_METADATA == True and timestamp is not None:
        metadata.timestamp = gdata.photos.Timestamp(text=timestamp)
        metadata.published = atom.Published(text=metadata.timestamp.isoformat())
        metadata.updated = atom.Updated(text=metadata.timestamp.isoformat())
        UpdateFileMetadata(filename, metadata.timestamp.datetime())

    if DRY_RUN == False:
        try:
            photo = gd_client.InsertPhoto( \
                url, metadata, filename, 'image/' + imageFormat)
            if photo is None:
                ERRORS.append('Photo may not have been uploaded: ' + filename)
        except gdata.photos.service.GooglePhotosException:
            ERRORS.append('Photo may not have been uploaded: ' + filename)

def AddFilesFromFolder(folder, summary, timestamp=None):
    log('Uploading images from folder: %s', folder)
    for content in os.listdir(folder):
        if os.path.isfile(folder + content):
            AddPhoto(folder + content,
                     summary,
                     content,
                     getImageExtension(folder + content),
                     timestamp)

def UploadPics(folder, summary=''):
    log('Folder: %s', folder)
    anyFileInFolder = \
        any(os.path.isfile(''.join([folder, i])) for i in os.listdir(folder))
    if anyFileInFolder == True:
        title = os.path.basename(os.path.normpath(folder))
        timestamp = GetTimestampFromFolderName(title)
        AddFilesFromFolder(folder, summary, timestamp)

    # recurse
    for content in os.listdir(folder):
        if os.path.isdir(folder + content):
            summary = content if not summary else (summary + ', ' + content)
            UploadPics( \
                folder + content + '/', summary.strip())

if __name__ == '__main__':
    RemoveFiles()
    # options for oauth2 login
    configdir = os.path.expanduser(CONFIG_DIR)
    client_secrets = os.path.join(configdir, CLIENT_SECRET_FILE)
    credential_store = os.path.join(configdir, CREDENTIAL_STORE_FILE)
    gd_client = OAuth2Login(client_secrets, credential_store, EMAIL_ADDRESS)

    DRY_RUN = True
    if MODE == 1:
        ShowAlbums()
    elif MODE == 2:
        log('Starting Job')
        UploadPics(PHOTO_DIR)
        WriteToFiles()
        log('Job Finished')
    elif MODE == 3:
        log('Starting Job')
        DRY_RUN = False
        UploadPics(PHOTO_DIR)
        WriteToFiles()
        log('Job Finished')
