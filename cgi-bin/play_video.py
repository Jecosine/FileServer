#!C:\Python27\python.exe
import cgi
import os


form = cgi.FieldStorage()

pattern = open('play_video.html','rb').read()
path = form.getvalue('path')
if path:
	filename = path.split('/')[-1]
	content = pattern % (filename,filename.split('.')[0],path)
	print content

