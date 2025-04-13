import os
import shutil
import sys
import bs4
import ffmpeg
import moviepy.editor as mpeditor
from css_html_js_minify import css_minify
from css_html_js_minify import js_minify
from css_html_js_minify import html_minify
from PIL import Image
import csv

MAX_DIMESIONS_EXEC = (120, 120)
MAX_DIMESIONS_GALLERY = (720, 720)
GALLERY_DIR = "gallery"
DIST_DIR = "dist"
SRC_DIR = "src"
USE_MP4 = True

for root, dirs, files in os.walk(SRC_DIR):
    for d in dirs:
        os.chmod(os.path.join(root, d), 0o777)
    for f in files:
        os.chmod(os.path.join(root, f), 0o777)

def handleHTML(srcPath, destPath, fileName):
    with open(srcPath) as f:
        text = f.read()
        soup = bs4.BeautifulSoup(text)

        gallery = soup.find(id="gallery-view")
        gallery.clear()

        for galleryIndex, galleryItem in enumerate(genGallery()):
            destName = galleryItem["filePath"]
            fileExtension = os.path.splitext(destName)[1][1:]
            galleryMedia = None

            if USE_MP4:
                if fileExtension == "mp4" or fileExtension == "gif":
                    destName = destName[:-len(fileExtension)]+"mp4"
                    galleryMedia = soup.new_tag("video")
                    galleryMedia["autoplay"], galleryMedia["muted"], galleryMedia["loop"], galleryMedia["playsinline"] = \
                        (None,) * 4
                    vid_src = soup.new_tag("source")
                    vid_src["src"] = os.path.join(GALLERY_DIR, destName)
                    vid_src["type"] = "video/mp4"
                    galleryMedia.append(vid_src)
                else:
                    galleryMedia = soup.new_tag("img")
                    galleryMedia["src"] = os.path.join(GALLERY_DIR, destName)
                    galleryMedia["loading"] = "lazy" # Lazy-load images
                    image = Image.open(os.path.join(SRC_DIR, GALLERY_DIR, destName))
                    galleryMedia["width"], galleryMedia["height"] = image.width, image.height
            else:
                if fileExtension == "mp4":
                    destName = destName[:-len(fileExtension)]+"gif"
                galleryMedia = soup.new_tag("img")
                galleryMedia["src"] = os.path.join(GALLERY_DIR, destName)

            galleryItem = soup.new_tag("div")
            galleryItem["onmouseenter"], galleryItem["class"]=\
                f"showOverlay(this,{galleryIndex})", "gallery-item"
            galleryMedia["class"] = "gallery-media"
            galleryItem.append(galleryMedia)
            gallery.append(galleryItem)
            
        text = html_minify(str(soup))
        makeTextFile(destPath, text)
        return [destPath]

def handleCSS(srcPath, destPath, fileName):
    with open(srcPath) as f:
        text = f.read()
        min_css = css_minify(text)
        makeTextFile(destPath, min_css)
        return [destPath]

def handleJS(srcPath, destPath, fileName):
    with open(srcPath) as f:
        galleryInfoLine = "var galleryInfo=["
        for galleryItem in genGallery():
            json = galleryItem.copy()
            del json["filePath"]
            galleryInfoLine += f"{json},"
        galleryInfoLine = galleryInfoLine[:-1]+"];"
        text = galleryInfoLine + f.read().split("\n", 1)[1]
        min_js = js_minify(text)
        makeTextFile(destPath, min_js)
        return [destPath]

def handleVideo(srcPath, destPath, fileName):
    width, height = mpeditor.VideoFileClip(srcPath).size
    vid = ffmpeg.input(srcPath).crop(0, 0, (width//2)*2, (height//2)*2)
    fileExtension = os.path.splitext(fileName)[1]
    if USE_MP4:
        destPath = destPath[:-len(fileExtension)] + ".mp4"
        save = lambda vid, path:\
            vid\
            .output(destPath, vcodec="libx264", format="mp4", video_bitrate=0, pix_fmt="yuv420p")\
            .run()
    
    save(vid, destPath)
    os.chmod(destPath, 0o777)
    return [destPath]

def handleImage(srcPath, destPath, fileName):
    if fileName.startswith("exec-"):
        image = Image.open(srcPath)
        for size in thumbnailSizes(image.width, image.height, [MAX_DIMESIONS_EXEC]):
            if size != None:
                image.thumbnail(size)
                image.save(destPath)
                return [destPath]
            else:
                return handleDefault(srcPath, destPath, fileName)
    elif "/gallery/" in srcPath:
        image = Image.open(srcPath)
        for size in thumbnailSizes(image.width, image.height, [MAX_DIMESIONS_GALLERY]):
            image.thumbnail(size)
            image.save(destPath)
            return [destPath]
    else: 
        return handleDefault(srcPath, destPath, fileName)

def handleDefault(srcPath, destPath, fileName):
    shutil.copyfile(srcPath, destPath, follow_symlinks=False)
    return [destPath]

def makeTextFile(path, contents):
    with open(path, "w") as f:
        f.write(contents)

def genGallery():
    def info(filePath, artist, description, shortDesc):
        return {
            "filePath": filePath, 
            "artist": artist, 
            "description": description, 
            "shortDesc": shortDesc
        }

    with open("gallery.csv") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader) # Skip column-name row
        galleryItems = [info(*row) for row in reader]
    return galleryItems

def thumbnailSizes(srcWidth, srcHeight, destSizes):
    for size in destSizes:
        if size[0] >= srcWidth or size[1] >= srcHeight: break
        yield size
    yield None

FILE_HANDLERS = {
    "html": handleHTML,
    "css": handleCSS,
    "js": handleJS,
    "mp4": handleVideo,
    "gif": handleVideo,
    "png": handleImage,
    "jpg": handleImage
}

# fileName: Name of file or directory, eg. "index.html" or "src"
# relPath: Path of file relative to source directory, eg. "src/img/favicon.png" would be "img/favicon.png"
# outDir: Directory to output to, usually "dist"; files are written to "{outDir}/{relPath}"
# srcDir: Source directory, usually "src"; files are located at "{srcDir}/{relPath}"
# return: list of output directories as relative paths
def handleFile(fileName, relPath, outDir, srcDir=SRC_DIR):
    print(relPath)

    srcPath = os.path.join(srcDir, relPath)
    destPath = os.path.join(outDir, relPath)
    if os.path.isdir(srcPath):
        os.makedirs(destPath, mode=0o777)
        for subFileName in os.listdir(srcPath):
            print(subFileName)
            _ = handleFile(subFileName, os.path.join(relPath, subFileName), outDir, srcDir)
        return [relPath]

    print(f"File to copy: {srcPath}")
    print(f"Destination: {destPath}")

    fileExtension = os.path.splitext(fileName)[1]
    if len(fileExtension) > 0: 
        fileExtension = fileExtension[1:]

    return FILE_HANDLERS.get(fileExtension, handleDefault) (srcPath, destPath, fileName)

def package():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    os.makedirs(DIST_DIR, mode=0o777, exist_ok=True)
    for fileName in os.listdir(SRC_DIR):
        handleFile(fileName, fileName, DIST_DIR, SRC_DIR)

def deploy():
    with open("remote-info.txt", "r") as f:
        info = f.read().split("\n")
        URL = info[0]
        ATHENA_USERNAME = info[1] if len(info) > 1\
            else input("Athena username to deploy with: ")
        SITE_DIR = f"{ATHENA_USERNAME}@{URL}"
        os.system(f"scp -r {DIST_DIR}/* {SITE_DIR}")

if "-deploy" in sys.argv:
    deploy()
elif "-package" in sys.argv:
    package()
else:
    package()
    deploy()
