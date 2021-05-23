#vBF2 style info map generater v1.1
#by worldlife

import sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import conParser

LEVELS_DIR = "levels" #for debug purposes
if not os.path.isdir(LEVELS_DIR): LEVELS_DIR = "..\\..\\levels" #installed in mod directory
NVDXT_PATH = "bin\\nvdxt.exe"
MAPPATH_COMBATAREA = "maps\\areas\\CombatArea.dds"
MAPPATH_COVER = "maps\\areas\\cover.png"
MAPPATH_FLAGS = "maps\\flags"
MAPPATH_FLAGS_CP_IMGNAME = "miniMap_CP.tga"
MAPPATH_FLAGS_CPBASE_IMGNAME = "utct.tga"#"miniMap_CPBase.tga"
OUTPUT_SIZE = (1024,1024)

BBOX_EXPAND_SCALE = 1.25

DRAW_COVER = True

DRAW_MINIMAP = True
MINIMAP_POSITION = (820,820)
MINIMAP_SIZE = (166,166)
MINIMAP_LINEWIDTH = 5
MINIMAP_BORDER_COLOR = (255,255,255,255)
MINIMAP_BOUNDINGBOX_COLOR = (255,0,0,255)

DRAW_PROJECTION_EFFECT = True
PROJECTION_VECTOR = (-6,6)
PROJECTION_BLUR = 3
PROJECTION_SHADOWCOLOR = (20,20,20,225)

class LevelInfo:
	def __init__(self, levelname):
		self.levelname = levelname
		self.mapsize = 1024
		self.teamnames = ["Neutral","Mec","Us"]

class CombatAreaInfo:
	def __init__(self, templateName):
		self.templateName = templateName
		self.points = []
		self.team = 0
		self.vehicles = 0
		
class ControlPointInfo:
	def __init__(self, templateName):
		self.templateName = templateName
		self.id = -1
		self.team = 0
		self.sequence = 0
		self.layer = 1
		self.AB = ''
		self.utct = 0
		self.showOnMinimap = 1
		self.position = (0,0,0)#'0/0/0'
		self.rotation = (0,0,0)#'0/0/0'

def findLevelInfo(levelpath):
	levelinfo = LevelInfo(os.path.split(levelpath)[-1])
	initcons = conParser.readCon(os.path.join(levelpath,"init.con"))
	print(initcons)
	heightcons = conParser.readCon(os.path.join(levelpath,"Heightdata.con"))
	for con in initcons:
		if con.get('gameLogic.setTeamName'):
			if int(con['gameLogic.setTeamName'][0])>0: levelinfo.teamnames[int(con['gameLogic.setTeamName'][0])] = con['gameLogic.setTeamName'][1].strip("\"")
	for con in heightcons:
		if con.get('heightmapcluster.setHeightmapSize'):
			levelinfo.mapsize = int(con['heightmapcluster.setHeightmapSize'][0])
	print("mapsize = %s" % levelinfo.mapsize)
	print("team1name = %s" % levelinfo.teamnames[1])
	print("team2name = %s" % levelinfo.teamnames[2])
	return levelinfo
		
def findGPOInfo(cons):		
	cps = {}
	combatAreas = {}
	usecombatarea = 1
	activeCATemplate = ''
	activeCpTemplate = ''#templateName
	activeCp = ''#templateName
	for con in cons:
		#cp info
		if len(activeCpTemplate) != 0 and con.get('ObjectTemplate.team'): 
			cps[activeCpTemplate].team = int(con['ObjectTemplate.team'][0])
			continue
		if len(activeCpTemplate) != 0 and con.get('ObjectTemplate.controlPointId'): 
			cps[activeCpTemplate].id = int(con['ObjectTemplate.controlPointId'][0])
			continue
		if len(activeCpTemplate) != 0 and con.get('ObjectTemplate.unableToChangeTeam'): 
			cps[activeCpTemplate].utct = int(con['ObjectTemplate.unableToChangeTeam'][0])
			continue
		if len(activeCpTemplate) != 0 and con.get('ObjectTemplate.showOnMinimap'):
			cps[activeCpTemplate].showOnMinimap = int(con['ObjectTemplate.showOnMinimap'][0])
			continue
		if con.get('ObjectTemplate.create'):
			if con['ObjectTemplate.create'][0] == "ControlPoint":
				activeCpTemplate = con['ObjectTemplate.create'][1]
				cps[activeCpTemplate] = ControlPointInfo(activeCpTemplate)
			continue
		if con.get('Object.create') and cps.get(con['Object.create'][0]):
			activeCp = con['Object.create'][0]
			continue
		if len(activeCp) != 0 and con.get('Object.absolutePosition'):
			cps[activeCp].position = tuple([float(a) for a in con['Object.absolutePosition'][0].split('/')])
			continue
		if len(activeCp) != 0 and con.get('Object.layer'):
			cps[activeCp].layer = int(con['Object.layer'][0])
			continue
		#combatarea
		if con.get('CombatAreaManager.use'):
			usecombatarea = int(con['CombatAreaManager.use'][0])
		if con.get('CombatArea.create'):
			activeCATemplate = con['CombatArea.create'][0]
			combatAreas[activeCATemplate] = CombatAreaInfo(activeCATemplate)
		if len(activeCATemplate) != 0 and con.get('CombatArea.addAreaPoint'):
			combatAreas[activeCATemplate].points.append(tuple([float(a) for a in con['CombatArea.addAreaPoint'][0].split('/')]))
		if len(activeCATemplate) != 0 and con.get('CombatArea.team'):
			combatAreas[activeCATemplate].team = int(con['CombatArea.team'][0])
		if len(activeCATemplate) != 0 and con.get('CombatArea.vehicles'):
			combatAreas[activeCATemplate].vehicles = int(con['CombatArea.vehicles'][0])
	cpinfo = [cps[cpname] for cpname in cps]
	
	combatareaPoints = []
	combatareaPointsSecondary = []
	for caName in combatAreas:
		if len(combatAreas[caName].points)>0 and combatAreas[caName].team==0: #only use vBF2 style combatArea
			if combatAreas[caName].vehicles==4: 
				combatareaPoints.append(combatAreas[caName].points)
			else:
				combatareaPointsSecondary.append(combatAreas[caName].points)
	if len(combatareaPoints) > 0:
		combatareaPoints = combatareaPoints[0] # TODO: maybe we can combine all valid CAs
	elif len(combatareaPointsSecondary) > 0:
		combatareaPoints = combatareaPointsSecondary[0]
	
	return cpinfo, combatareaPoints

#convert and open dds which is not in dxt* format and cannot be opened by pillow	
def convertDDS(filepath, outputFile=None):
	if os.path.exists(filepath):
		if not outputFile: outputFile = "\\".join((os.getcwd(),"tmp\\"+os.path.basename(filepath))) #save as tmp file
		if not os.path.exists(outputFile):
			cmd = NVDXT_PATH + " -file \"" + "\\".join((os.getcwd(),filepath)) + "\" -dxt1c -nomipmap -output \"" + outputFile + "\""
			os.system(cmd)
		return Image.open(outputFile)
	else:
		return None

#vBF2 info maps use dds dxt1 instead of png(but with .png suffix, why??)
def convertOutputMaps(outputPath):
	print("Converting output...")
	if os.path.isdir(outputPath):
		cmd = NVDXT_PATH + " -file \"" + "\\".join((os.getcwd(),outputPath)) + "\\*menuMap.png\" -dxt1c -nomipmap -outsamedir"
		os.system(cmd)
		os.system("copy /y \"" + "\\".join((os.getcwd(),outputPath)) + "\\*.dds\" \"" + "\\".join((os.getcwd(),outputPath)) + "\\*.png\" ")
		os.system("del \"" + "\\".join((os.getcwd(),outputPath)) + "\\*.dds\"")

#convert coordinates in game to image coordinates
def convertCoord(coord, imgsize, mapsize):
	if len(coord)==2:
		return (int(coord[0]/mapsize*imgsize+imgsize/2),int(-coord[1]/mapsize*imgsize+imgsize/2))	
	else:
		return (int(coord[0]/mapsize*imgsize+imgsize/2),int(-coord[2]/mapsize*imgsize+imgsize/2))#get x,z from 3d point

#convert coordinates in game to image coordinates in cropped image
def convertCoordCropped(coord, imgsize, mapsize, cropbox):
	imgCoord = convertCoord(coord, imgsize, mapsize)
	normCropCoord = ((imgCoord[0]-cropbox[0]+0.0)/(cropbox[2]-cropbox[0]), (imgCoord[1]-cropbox[1]+0.0)/(cropbox[3]-cropbox[1]))
	return (int(normCropCoord[0]*OUTPUT_SIZE[0]), int(normCropCoord[1]*OUTPUT_SIZE[1]))		

#get bounding box around the combatarea to crop
def getBoundingBox(coords, imgsize, mapsize):
	left, top, right, bottom = imgsize,imgsize,0,0
	if len(coords)==0: return 0,0,imgsize,imgsize
	for coord in coords:
		coord = convertCoord(coord, imgsize, mapsize)
		if coord[0]<left: left=coord[0]
		if coord[0]>right: right=coord[0]
		if coord[1]<top: top=coord[1]
		if coord[1]>bottom: bottom=coord[1]
	#expand box to BBOX_EXPAND_SCALE-scaled square
	size = int(max(bottom-top,right-left) * BBOX_EXPAND_SCALE)
	#if the combatarea is big enough, use the whole image
	if size>imgsize: return 0,0,imgsize,imgsize
	center = [(right+left)/2,(top+bottom)/2]
	# edgeDist = (min(center[0],imgsize-center[0]),min(center[1],imgsize-center[1]))
	# if the bbox reaches the edge, we try to adjust the center
	# if size>edgeDist[0]*2: center[0] = size/2
	# if size>edgeDist[1]*2: center[1] = size/2
	if size>center[0]*2: center[0] = size/2
	if size>(imgsize-center[0])*2: center[0] = imgsize-size/2
	if size>center[1]*2: center[1] = size/2
	if size>(imgsize-center[1])*2: center[1] = imgsize-size/2
	return center[0]-size/2, center[1]-size/2, center[0]+size/2, center[1]+size/2

def drawRect(dc, box, fill, width):
	dc.line([\
		(box[0],box[1]),\
		(box[2],box[1]),\
		(box[2],box[3]),\
		(box[0],box[3]),\
		(box[0],box[1]),\
		],fill,width)

#draw shadow effect
def drawProjectionCanvas(canvas):
	shadowalpha = canvas.split()[3]#get the alpha channel
	shadowalpha = ImageChops.offset(shadowalpha,PROJECTION_VECTOR[0],PROJECTION_VECTOR[1])#move to projection
	shadowalpha = shadowalpha.filter(ImageFilter.GaussianBlur(PROJECTION_BLUR))#blur
	shadowCanvasBands = list(Image.new('RGBA', canvas.size, PROJECTION_SHADOWCOLOR).split())
	shadowCanvasBands[3] = ImageChops.multiply(shadowalpha,shadowCanvasBands[3])#apply alpha channel
	return Image.merge('RGBA',shadowCanvasBands)

#parse a gpo.con and output an info image
def parseCon(levelinfo, gamemode, playernum):
	cons = conParser.readCon(LEVELS_DIR + "\\" + "\\".join((levelinfo.levelname, "gamemodes", gamemode, playernum, "gameplayobjects.con")))
	cps, combatareaPoints = findGPOInfo(cons)
	#create base image
	baseimg = None
	try:
		baseimg = Image.open(LEVELS_DIR + "\\" + levelinfo.levelname + "\\hud\\minimap\\ingameMap.dds")
	except:
		#if cannot open, try to convert dds to DXT1 format
		baseimg = convertDDS(LEVELS_DIR + "\\" + levelinfo.levelname + "\\hud\\minimap\\ingameMap.dds")
		if not baseimg: 
			print("Image %s not found!" % (LEVELS_DIR + "\\" + levelinfo.levelname + "\\hud\\minimap\\ingameMap.dds"))
			return	
	baseSize = baseimg.size[0] # use this for coordinate conversion
	#prepare drawing maps
	try:
		cpmaps = [Image.open(("\\".join((MAPPATH_FLAGS,teamname,MAPPATH_FLAGS_CP_IMGNAME)))) for teamname in levelinfo.teamnames]
	except IOError:
		print("One of the team's flag cannot be found!")
		return
	#cpbasemaps = [Image.open("\\".join((MAPPATH_FLAGS,teamname,MAPPATH_FLAGS_CPBASE_IMGNAME))) for teamname in levelinfo.teamnames]
	cpbasemap = Image.open(("\\".join((MAPPATH_FLAGS,MAPPATH_FLAGS_CPBASE_IMGNAME))))
	#crop around the combat area and resize image
	caBox = getBoundingBox(combatareaPoints, baseSize, levelinfo.mapsize)
	img = baseimg.crop(caBox).resize(OUTPUT_SIZE,resample=Image.BILINEAR)
	
	#draw combat area
	caImg = Image.open(MAPPATH_COMBATAREA).resize(OUTPUT_SIZE,resample=Image.BILINEAR)
	#draw a polygon on combat area's alpha channel
	polyPts = [convertCoordCropped(pt, baseSize, levelinfo.mapsize, caBox) for pt in combatareaPoints]
	if len(polyPts)>2:
		dc = ImageDraw.Draw(caImg)# get a drawing context
		dc.polygon(polyPts, fill=(0,0,0,0))
	if caImg.size != img.size: caImg = caImg.resize(img.size,resample=Image.BILINEAR)
	img = Image.alpha_composite(img,caImg)
		
	#draw controlPoints
	cpCanvas = Image.new('RGBA', img.size, (255,255,255,0))
	for cp in cps:
		if cp.showOnMinimap==0: continue
		newCanvas = Image.new('RGBA', img.size, (255,255,255,0))
		drawmap = cpmaps[cp.team] #if cp.utct==0 else cpbasemaps[cp.team]
		cpPos = convertCoordCropped(cp.position, baseSize, levelinfo.mapsize, caBox)
		drawPos = (int(cpPos[0]-drawmap.size[0]/2), int(cpPos[1]-drawmap.size[1]/2)) #draw at center
		if cp.utct!=0: 
			drawmap = Image.alpha_composite(cpbasemap,drawmap)#cpCanvas.paste(cpbasemap,drawPos)
		newCanvas.paste(drawmap,drawPos)	
		cpCanvas = Image.alpha_composite(cpCanvas, newCanvas)
	#add projection effect(alt:add in photoshop)
	if DRAW_PROJECTION_EFFECT:
		shadowCanvas = drawProjectionCanvas(cpCanvas)
		#img = Image.composite(shadowCanvas, img, shadowalpha)
		img = Image.alpha_composite(img,shadowCanvas)
	img = Image.alpha_composite(img,cpCanvas)
	
	#draw cover(grid, boarders, decorations, etc.)
	if DRAW_COVER:
		coverImg = Image.open(MAPPATH_COVER)
		if coverImg.size != img.size: coverImg = coverImg.resize(img.size,resample=Image.BILINEAR)
		img = Image.alpha_composite(img,coverImg)
	
	#draw minimap
	#prepare minimap and canvas
	if DRAW_MINIMAP:
		minimap = baseimg.resize(MINIMAP_SIZE,resample=Image.BILINEAR)
		minimapCanvas = Image.new('RGBA', img.size, (255,255,255,0))
		dc = ImageDraw.Draw(minimapCanvas)# get a drawing context
		#draw border
		borderbox = (MINIMAP_POSITION[0],MINIMAP_POSITION[1],MINIMAP_POSITION[0]+MINIMAP_SIZE[0],MINIMAP_POSITION[1]+MINIMAP_SIZE[1])
		drawRect(dc, borderbox, MINIMAP_BORDER_COLOR, MINIMAP_LINEWIDTH)
		#draw combat area bounding box on minimap
		mndc = ImageDraw.Draw(minimap)
		miniCABox = [int((coord+0.0)/baseSize*MINIMAP_SIZE[0]) for coord in caBox] #MAY NEED FIX!
		drawRect(mndc, miniCABox, MINIMAP_BOUNDINGBOX_COLOR, MINIMAP_LINEWIDTH)
		#draw minimap
		#dc.bitmap(MINIMAP_POSITION,minimap)
		minimapCanvas.paste(minimap,MINIMAP_POSITION)
		#add projection effect
		if DRAW_PROJECTION_EFFECT:
			shadowCanvas = drawProjectionCanvas(minimapCanvas)
			img = Image.alpha_composite(img,shadowCanvas)
		img = Image.alpha_composite(img,minimapCanvas)
	
	#save image
	if gamemode[0:2]=="sp": gamemode="sp1"#all sp use sp1
	saveName = LEVELS_DIR + "\\" + "\\".join((levelinfo.levelname,"info")) + "\\" + "_".join((gamemode, playernum, "menumap.png"))
	print("Saving %s..." % saveName)
	img.convert('RGB').save(saveName)#convert to RGB
	#convert to dds format(do this after the level is done)
	#convertDDS(saveName,saveName)

def processLevel(level):
	print("Processing level %s..." % level)
	levelpath = os.path.join(LEVELS_DIR,level) 
	if os.path.isdir(levelpath):
		levelinfo = findLevelInfo(levelpath)
		gmspath = os.path.join(levelpath,"gamemodes")
		if os.path.isdir(gmspath):
			for gamemode in os.listdir(gmspath):
				gmpath = os.path.join(gmspath,gamemode)  
				if os.path.isdir(gmpath):
					for playernum in os.listdir(gmpath):
						parseCon(levelinfo, gamemode, playernum)
				else: print("No layer found in %s!" % gmpath)
			convertOutputMaps(LEVELS_DIR + "\\" + "\\".join((levelinfo.levelname,"info")))
		else: print("No gamemodes found in %s!" % gmspath)		
	else:
		print("Level %s not valid!" % level)
		
def main():
	hasLevel = False
	if not os.path.isdir(LEVELS_DIR): print("No Levels folder detected! Check your installation!")
	for levelname in os.listdir(LEVELS_DIR): 
		if not hasLevel:
			hasLevel = True
			print("Levels detected...")
		print("--> %s" % levelname)
	if not hasLevel: 
		print("No level detected!")
		os.system("pause")
		return
	print("Input the level name you want to generate info maps(input \"all\" to generate for all levels):")
	if sys.version_info[0] >= 3:
		input_str = input()
	else:
		input_str = raw_input()
	# create tmp folder if it does not exist
	if not os.path.exists("tmp"): os.mkdir("tmp")
	# clear tmp folder
	for file in os.listdir("tmp"): os.remove("\\".join(("tmp",file)))
	if input_str=="all":
		for levelname in os.listdir(LEVELS_DIR):
			processLevel(levelname)
			for file in os.listdir("tmp"): os.remove("\\".join(("tmp",file)))
	else:
		processLevel(input_str)
	os.system("pause")
	
if __name__ == "__main__":
	main()