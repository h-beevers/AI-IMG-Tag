Image Tagger
A desktop GUI tool for batch metadata tagging of images.
Select a folder (including nested subfolders), preview total images and estimated tagging time, then automatically run through your tag suggestion, manual review, and ExifTool metadata writing pipeline—all in one responsive application.

Features
- Recursive folder scan for common image types (.jpg, .png, .bmp, .webp, etc.)
- Preview dialog showing:
- Total images found
- Estimated tagging time (configurable average per image)
- Threaded folder scanning for a nonblocking GUI
- Confirmation prompt before batch load
- Single-image view with “Prev”/“Next” navigation
- On-demand tag suggestions via Ollama LLM
- Manual tag entry and save to metadata with ExifTool
- Batch review window with scrollable thumbnails and editable tag boxes
- Automatic deduplication and ASCII normalization of tags
- Error logging to tagger_errors.log

Requirements
- Python 3.8+
- Tkinter (included in most Python installs)
- Pillow (pip install pillow)
- Ollama Python client (pip install ollama)
- ExifTool (exiftool.exe on Windows; downloaded separately)

Installation
- Clone or download this repository.
- Ensure ExifTool is installed and note its installation path.
- Install Python dependencies:
pip install pillow ollama
- Place Image_Tagger.py in your working directory.

ExifTool
ExifTool must be installed separately for writing metadata:
1. 	Download from https://exiftool.org
2. 	Place  in a folder on PATH or note its location for manual selection
3. 	Optionally set an environment variable:

How to Use
1. Load Folder
1. 	Click Load Folder
2. 	Select the directory containing your images
3. 	Confirm image count and estimated tagging time
The first time you load, the app will locate or ask for your  path.

2. Single-Image Tagging
1. 	Use << Prev and Next >> to navigate through images
2. 	Click Suggest Tags to fetch AI-generated keywords
3. 	Edit the tag list in the text field if needed
4. 	Click Save Tags to write metadata with ExifTool
Progress and errors appear in the status bar. Detailed logs are written to .

3. Batch Review & Apply
1. 	After loading, click Batch Review All
2. 	Wait as AI suggestions generate, with a progress bar and ETA
3. 	In the review window:
• 	Scroll through thumbnails and suggested tags
• 	Edit any tag boxes
• 	Use the checkboxes to include or exclude images
4. 	Click Apply Selected or Apply All
5. 	Wait for the apply-progress bar to complete
Once done, the window closes and a confirmation dialog appears.

Troubleshooting
• 	If ExifTool fails, verify  is reachable or manually browse when prompted
• 	Missing Python modules? Re-run  in the same environment
• 	On packaged EXE, errors may surface in a pop-up; review  for full trace
