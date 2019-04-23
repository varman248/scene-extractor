# IMPORT MODULES AND FUNCTIONS
import re, subprocess, math
from os import makedirs, pardir, path, listdir, system, remove
from os.path import exists, dirname, realpath, abspath, join, isfile, basename, splitext
import numpy as np

class Path:

	def __init__(self):
		# GET CURRENT AND MAIN PATH
		self.current = dirname(realpath(__file__))
		self.config()
		path_ffmpeg = self.settings['ffmpeg']
		self.ffmpeg = join(path_ffmpeg, 'ffmpeg.exe')
		self.ffprobe = join(path_ffmpeg, 'ffprobe.exe')
		# SET OTHERS PATH
		self.cache = self.dir_set(join(self.current, "cache"))
		self.keep = self.dir_set(join(self.current, "keep"))
		self.cut = self.dir_set(join(self.current, "cut"))
		self.video = self.dir_set(join(self.current, "video"))
		self.merge = self.dir_set(join(self.current, "merge"))
		self.screenshot = self.dir_set(join(self.current, "screenshot"))
		self.files = self.dir_files(self.video)
		self.check();

	def config(self, separator=':::'):
		self.config = self.file_set(join(self.current, "config.txt"))
		# SET DEFAULT VALUE
		default = {
				'ffmpeg': r'C:\Users\varma\software\ffmpeg\bin',
				'change': .4,
				}
		# GET CONFIG FILE LINES
		settings = {}
		with open(self.config) as f:
			txt = [line.rstrip('\r\n').split(separator) for line in f if ':' in line]
		for e in txt:
			settings[e[0]] = e[1]
		# UPDATE CONFIG
		default.update(settings)
		self.settings = default
		# UPDATE CONFIG FILE
		txt = open(self.config, "w")
		for k, v in self.settings.items():
			line = separator.join([str(k), str(v)])
			txt.write(line+"\n")

	def reset(self):
		for folder in [self.cache, self.cut, self.merge, self.screenshot]:
			self.dir_empty(folder)

	def cache_file(self, filename):
		return self.file_set(join(self.cache, filename))

	def file_set(self, path):
		if not isfile(path):
			open(path, 'a').close()
		return path

	def dir_set(self, path):
		if not exists(path):
			makedirs(path)
		return path

	def dir_files(self, path):
		return [join(path, f) for f in listdir(path) if isfile(join(path, f))]

	def dir_empty(self, path):
		for file in self.dir_files(path):
			remove(file)

	def check(self):
		# IF VIDEO DOES NOT EXIST
		if not self.files:
			raise Exception("---> No video in the folder !")

	def cmd(self, cmd, name="cmd_lines", pause=False):
		self.clip = self.cache_file("clip.txt") 
		path = join(self.cache, name+".bat")
		file = open(self.clip,"w+")
		file.write(path+"\n")
		file.close()
		if not isinstance(cmd, list):
			lst = [cmd] 
		else: 
			lst = cmd
		if pause == False:
			lst = lst + ['exit'] 
		else:
			lst = lst + ['pause']
		file = open(path,"w+")
		for x in lst:
			file.write(x+"\n")
		file.close()
		system(path)
		


class Interval:

	def __init__(self, t1, t2):
		self.a = t1
		self.b = t2

	def cut(self, n):
		d = abs(self.a-self.b)/n
		return [x for x in np.arange(self.a, self.b, d)]+[self.b]


class Sequences:

	def sequences(self, seqs):
		self.seqs = seqs

	def pts(self, pts):
		pts.sort()
		self.seqs = [Interval(pts[i], x) for i, x in enumerate(pts[1:])]

	def files(self, files):
		seqs = []
		for file in files:
			name = basename(file)
			its = splitext(name)[0].replace(',', '.').split('_')
			seqs.append(Interval(float(its[0]), float(its[1])))
		self.seqs = seqs

	def cut(self, n):
		return [i.cut(n) for i in self.seqs]

	def merge(self):
		pts = [p for itv in self.seqs for p in [itv.a, itv.b]]
		pts.sort()
		pts = [p for p in pts if pts.count(p) == 1]
		self.seqs = [Interval(pts[i-1], pts[i]) for i in range(1, len(pts), 2)]
		




class FFMPEG:
	
	def __init__(self):
		self.path = Path()
		self.seqs = Sequences()
		self.file = self.path.files[0]
		# Get Duration From Video File
		sh = subprocess.check_output([
			self.path.ffprobe, '-v', 'error', '-show_entries', 'format=duration', 
			'-of', 'default=noprint_wrappers=1:nokey=1', self.file
			])
		self.duration = eval(str(sh, 'utf-8'))
		# Get FPS From Video File
		sh = subprocess.check_output([
			self.path.ffprobe, '-v', 'error', '-select_streams', 'v', '-of', 
			'default=noprint_wrappers=1:nokey=1', '-show_entries', 
			'stream=r_frame_rate', self.file
			])
		s = str(sh, 'utf-8')
		self.fps = eval(s)

	def extract(self, e=5, convert=False):
		self.seqs.merge()
		# CHOOSE ACTION
		action = ' -c:v copy -c:a copy '
		if convert:
			action = ' -vcodec libx264 -crf 20 -preset fast -sn '
			e = 0
		# CREATE CMD FOR EACH INTERVAL
		cmds = []
		for i, seq in enumerate(self.seqs.seqs):
			cut = ' -ss '+str(round(seq.a-e, 2))+' -to '+str(round(seq.b, 2))+' '
			file = ' -i '+self.file
			out = join(self.path.cut, str(i)+'_'+basename(self.file))
			cmd = self.path.ffmpeg + cut + file + action + out
			cmds.append(cmd)
		# EXECUTE CMDS
		self.path.cmd(cmds, name='copy')

	def merge(self):
		self.path.list = self.path.cache_file("list.txt") 
		# WRITE LIST OF FILES TO MERGE INTO LIST
		txt = open(self.path.list,"w+") 
		for file in self.path.dir_files(self.path.cut):
			txt.write('file '+"'"+file+"'"+"\n")
		txt.close()
		# CREATE CMD FROM LIST FILE
		out = join(self.path.merge, 'merge_'+basename(self.file))
		cmd = self.path.ffmpeg + " -safe 0 -f concat -i " + self.path.list + " -c copy " + out
		self.path.cmd(cmd, name="merge")

	def change(self):
		ratio = self.path.settings['change']
		self.path.pts = self.path.cache_file("pts.txt") 
		select = r" -vf select=gt(scene\,"+ str(ratio) +")"
		info = ",showinfo -f null - 2> " + self.path.pts
		file = " -i " + self.path.files[0]
		cmd = self.path.ffmpeg + file + select + info
		self.path.cmd(cmd, name='screenshot')

	def import_pts(self):
		self.path.pts = self.path.cache_file("pts.txt") 
		with open(self.path.pts) as f:
			pts = [float(i) for line in f for x in re.findall("pts_time:[0-9.]*", line) for i in re.findall("[0-9.]*", x) if i]
		self.pts = [0] + pts + [self.duration]
		self.seqs.pts(self.pts)

	def import_screenshot(self):
		files = self.path.dir_files(self.path.screenshot)
		self.seqs.files(files)

	def screenshot(self, n=9):
		# EMPTY SCREENSHOT FOLDER
		self.path.dir_empty(self.path.screenshot)
		# CUT EACH SEQ
		itv = self.seqs.cut(n)
		# INTERVAL INTO MINI GROUPS
		group = [itv[x:x+10] for x in range(0, len(itv), 10)]
		# CREATE CMD FOR EACH SEQ
		cmds = []
		for seq in group:
			cmd = self.path.ffmpeg+' -i '+ self.file
			for v in seq:
				frames = [round(x*self.fps) for x in v]
				images = "".join([r"+eq(n\,"+str(f)+r")" for f in frames])
				name = str(round(v[0], 2))+'_'+str(round(v[-1], 2))
				name = name.replace(".", ",")
				out = join(self.path.screenshot, name+'.bmp')
				cel = str(int(math.sqrt(n)))
				grid = ",scale=320:-1,tile="+cel+"x"+cel+" -frames:v 1 "
				cmd = cmd + " -vf select='" + images + "'" + grid + " "+ out
			cmds.append(cmd)
		self.path.cmd(cmds, name='screenshot')

# -------------------------------------------------------------

#ffmpeg = FFMPEG()

#ffmpeg.change()
# ffmpeg.import_pts()
# ffmpeg.screenshot()

# ffmpeg.import_screenshot()
# ffmpeg.extract(convert=True)
# ffmpeg.merge()

# ffmpeg.path.reset()

# ffmpeg.seqs.merge()

