The different pieces of this repository allow me, from a device running iOS, to create a PDF containing the Japanese lyrics of a song. Furigana are added to the lyrics.

Here follows a brief description of how the several pieces interact:

- iOS Shortcut
	-	Captures the title, artist, and lyrics of a song.
- Python script, run from Pythonista
	-	Embeds song info into a upLaTEX template.
- iOS Shortcut
	-	Saves .tex file to any location; can save to personal server through the FileBrowser app.
- inotifywait watch script
	-	Compiles .tex files to PDF.
	-	Moves PDFs to a servable folder.
- NGINX server
	-	Serves PDFs.

The NGINX server configuration is dead simple, and thus has no place in this repository.

Can also get shortcut from: https://www.icloud.com/shortcuts/3cbbbe3278ba42d4b92005f1fc83ee5a

While the shorcut currently works as is, it lacks comments and might be in need of extra failsafes for public release.