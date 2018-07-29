import posixpath
import mimetypes
def guess_type(path):
		"""Guess the type of a file.

		Argument is a PATH (a filename).

		Return value is a string of the form type/subtype,
		usable for a MIME Content-type header.

		The default implementation looks the file's extension
		up in the table extensions_map, using application/octet-stream
		as a default; however it would be permissible (if
		slow) to look inside the data to make a better guess.

		"""
		if not mimetypes.inited:
			mimetypes.init() # try to read system mime.types
		extensions_map = mimetypes.types_map.copy()
		extensions_map.update({
			'': 'application/octet-stream', # Default
			'.py': 'text/plain',
			'.c': 'text/plain',
			'.h': 'text/plain',
			'.js':'text/plain',
			'.ogg':'video/ogg'
			})
		base, ext = posixpath.splitext(path)
		if ext in extensions_map:
			return extensions_map[ext]
		ext = ext.lower()
		if ext in extensions_map:
			return extensions_map[ext]
		else:
			return extensions_map['']

	