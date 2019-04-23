from ffmpeg import *

ffmpeg = FFMPEG()

ffmpeg.import_screenshot()
ffmpeg.extract(convert=True)