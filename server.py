#Import system operating modules
import os
import sys
import re
import posixpath
import shutil
#Import network related modules
import urllib
import urlparse
import re
import cgi
import BaseHTTPServer,SimpleHTTPServer,CGIHTTPServer

#Import code operating tools
import mimetypes
try:
	from StringIO import StringIO
except:
	from cStringIO import StringIO

class HttpRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):
	
	"""This Http request handler bases on SimpleHTTPRequestHandler,
	supporting file upload and download.Common Usage is similar to
	SimpleHTTPRequestHandler.
	"""
	def do_POST(self):
		if self.is_cgi():
			self.run_cgi()
		stat, info = self.process_data()
		print info,"from: %s" % str(self.client_address)
		#Show post status page
		html = open('post_status.html','rb')
		content = html.read()
		message = stat and "Success: " or "Failed: "
		returnLink = self.headers['referer']
		f = StringIO()
		f.write(content % (message, message+info, returnLink))
		length = f.tell()
		#Clear f
		f.seek(0)
		self.send_response(200)
		self.send_header("Content-type","text/html")
		self.send_header("Content-Length",str(length))
		self.end_headers()
		if f:
			self.copyfile(f, self.wfile)
			f.close()
	def send_head(self):
		"""Version of send_head that support CGI scripts"""
		if self.is_cgi():
			return self.run_cgi()
		else:
			return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)		
		
	def process_data(self):
		"""Check posting data,return a tuple (True/False,ErrorMessage)
		Structure of package:
		|//Content in self.headers e.g. content-length, boundary
		| Header Informations
		| ...
		|
		-------------------------------------------------------------
		|//Content in self.rfile:
		| {boundary}
		| Content-Disposition: ... name="file"; filename="..."
		| Content-Type: ... 
		| 
		| {data}
		| {boundary} //if is 'multipart'
		| Content-Disposition: ...
		| Content-Type: ...
		| 
		| {data}
		
		"""
		
		boundary = self.headers.plisttext.split('=')[1]
		remain = int(self.headers['content-length'])
		
		#Check whether file is started with boundary
		line = self.rfile.readline()
		remain -= len(line)
		if boundary not in line:
			return False,"File does not begin with boundary."
		
		#Get disposition info		
		line = self.rfile.readline()
		remain -= len(line)
		
		#Check file info 
		filename = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"',line)
		if not filename:
			return False,"Missing file name."
		path = self.translate_path(self.path)
		print path
		filename = os.path.join(path,filename[0])
		
		#Check whether file name exists
		while os.path.exists(filename):
			filename = filename.split('.')[0]+'+'+filename.split('.')[1]
			
		
		#Get content type info
		line = self.rfile.readline()
		remain -= len(line)
		filetype = re.findall(r'Content-Type: (.*).*',line)
		line = self.rfile.readline() #it is an empty line
		remain -= len(line)
		
		#Content begins, try writing data to file in server
		try:
			output = open(filename,'wb')
		except IOError:
			return False,"Authority denied."
		
		#Write data
		firstline = self.rfile.readline()
		remain -= len(firstline)
		while remain > 0:
			line = self.rfile.readline()
			remain -= len(line)
			if boundary in line:
				firstline = firstline[0:-1]
				if firstline[-1] == '\r':
					firstline = firstline[0:-1]
				output.write(firstline)
				output.close()
				return True,"File created.Path: %s" % filename
			else:
				output.write(firstline)
				firstline = line
		return False,"Unexpected file end."
	
	def list_directory(self, path):
		"""Referred from SimpleHTTPRequestHandler.py and do overriding 
		Helper to produce a directory listing (absent index.html).
		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().
		"""
		try:
			list = os.listdir(path)
		except os.error:
			self.send_error(404, "No permission to list directory")
			return None
		list.sort(key=lambda a: a.lower())
		f = StringIO()
		displaypath = cgi.escape(urllib.unquote(self.path))
		
		# f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
		# f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
		# f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
		# f.write("<hr>\n")
		# f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
		# f.write("<input name=\"file\" type=\"file\"/>")
		# f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
		# f.write("<hr>\n<ul>\n")
		html = open('Main.html','rb').read()
		filelist = ""
		for name in list:
			fullname = os.path.join(path, name)
			displayname = linkname = name
			# Append / for directories or @ for symbolic links
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			if os.path.islink(fullname):
				displayname = name + "@"
				# Note: a link to a directory displays with @ and links with /
			filelist += self.generate(linkname,displayname)
			"""<tr>
				<td style="width:2em;"><input class="check" type="checkbox" name="check_box_post" value="%s" /></td><td><dd><a href="cgi-bin/play_video.py?path=%s">%s</a></dd></td>
				
				</tr> % ('/'+urllib.quote(linkname), '/'+urllib.quote(linkname), cgi.escape(displayname))"""
		# f.write("</ul>\n<hr>\n</body>\n</html>\n")
		html = html % filelist
		f.write(html)
		length = f.tell()
		f.seek(0)
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.send_header("Content-Length", str(length))
		self.end_headers()
		return f
	def generate(self,linkname,displayname):
		"""Generate difference link.
		example return:
		a.txt -> "text/plain"
		a.jpg -> "image/jpeg"
		a.mp4 -> "video/mp4"
		a.xxx -> "application/octet-stream"
		"""	
		supported = ['mp4','ogg','webm']
		method = """<tr>
				<td style="width:2em;"><input class="check" type="checkbox" name="check_box_post" value="%s" /></td>
				<td><dd><div class="file_icon" style="background-image: url(/img/%s)"></div><a href="%s">%s</a></dd></td>				
				</tr>"""
		filetype = self.guess_type(linkname).split('/')
		classify = filetype[0]
		if linkname[-1] <> "/":
			if classify == "text":
				return method % ('/'+urllib.quote(linkname),"file_normal.png",'/cgi-bin/view_text.py?path=/'+urllib.quote(linkname), cgi.escape(displayname))
			elif classify == "video":
				return method % ('/'+urllib.quote(linkname),"video_normal.png",'/cgi-bin/play_video.py?path=/'+urllib.quote(linkname), cgi.escape(displayname))
			elif classify == "image" :
				return method % ('/'+urllib.quote(linkname),"landskape_normal.png",'/cgi-bin/view_text.py?path=/'+urllib.quote(linkname), cgi.escape(displayname))
			else:
				classify == "unknown"
				return method % ('/'+urllib.quote(linkname),"help_normal.png",urllib.quote(linkname), cgi.escape(displayname))
		elif linkname[-1] == "/":
			return method % ('/'+urllib.quote(linkname),"folder_normal.png",urllib.quote(linkname), cgi.escape(displayname))
	def guess_type(self,path):
		"""Guess the type of a file.

		Argument is a PATH (a filename).

		Return value is a string of the form type/subtype,
		usable for a MIME Content-type header.

		The default implementation looks the file's extension
		up in the table extensions_map, using application/octet-stream
		as a default; however it would be permissible (if
		slow) to look inside the data to make a better guess.

		"""
		
		base, ext = posixpath.splitext(path)
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		ext = ext.lower()
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		else:
			return self.extensions_map['']

	if not mimetypes.inited:
		mimetypes.init() # try to read system mime.types
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
			'': 'application/octet-stream', # Default
			'.py': 'text/plain',
			'.c': 'text/plain',
			'.h': 'text/plain',
			'.js':'text/plain',
			'.ogg':'video/ogg',
			})
	
BaseHTTPServer.test(HttpRequestHandler,BaseHTTPServer.HTTPServer)		
















