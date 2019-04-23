# scene-extractor

It's a tool that allows you to extract cut scenes from a video.

# requirements

- install Python 3 and numpy module
- download FFMPEG
- change FFMPEG folder path in scene-extractor/config.txt

Note: all files and folders are automatically generated except python files!

# how it works

- you can specify the ratio of change between 0 and 1 in scene-extractor/config.txt
- change.py will make screenshots of cut scenes
- you can delete unwanted scenes by deleting screenshots.
- copy.py or convert.py will extract scenes from screenshot folder into the cut folder 
- merge.py will merge extracted files in merge folder
