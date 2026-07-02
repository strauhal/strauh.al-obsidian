---
title: "printing videos"
source_kind: "html"
source_file: "/sessions/elegant-serene-archimedes/mnt/GitHub/strauh.al4/printing_videos.html"
source_relpath: "printing_videos.html"
compiled: "True"
compiled_at: "2026-07-01T18:01:48"
tags: ["strauhal", "source/html"]
---
# printing videos

Source: [[media/strauh.al4/printing_videos.html|source file]]

Concepts: [[HTML Source]], [[printing videos]], [[strauh.al Archive]]

## Compiled Page

strauh.al/printing_videos

# [strauh.al](https://strauh.al)/printing_videos

[visual differences between inkjet and laser printers](https://www.youtube.com/watch?v=_rR1-n8o67s)

## how to print videos

 requirements: a printer, a scanner, adobe after effects and photoshop, macOS strongly recommended (optional: chatGPT account)
 disclaimer: this is the way I print my videos; it may be a bit too convoluted so if you find a better way, feel free to tell me via email ([ernest@strauh.al](mailto:ernest@strauh.al))

## step 1: adobe stuff

 1a) install after effects and photoshop (and premiere pro if you want to add audio to your videos or do further arranging/cutting)

 1b) take any video file (mp4, mov, etc) and drop it into adobe after effects (add any effects if desired)

 1c) crop the video into a perfect square (this can be done through composition settings or by pressing ctrl-k or cmd-k)

 1d) go to file > export > add to render que

 1e) there should be a bunch of options. I usually go with 30 or 15 frames per second

 1f) this part is important: you want to export the video as a tiff or png sequence instead of a normal video file
 also check the “put in subfolder option” this should make organization easy.

## step 2: homebrew, python, libraries…

 ***If you run into any issues during this part, just copy and paste the errors into chatgpt and follow the instructions from there

 2a) install homebrew (open terminal and enter the text below)

 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

 2b) install python3 (through homebrew in terminal)

 brew install python3

 2c) then install pip (also in terminal)

 python3 get-pip.py

 2d) then install the Pillow library (using pip3; still in terminal land)

 pip3 install Pillow

 if pip3 install Pillow doesn't work, use brew install Pillow

 (if the terminal throws an error and says “Consider using the `--user` option or check the permissions" just copy and paste --user at the end

## step 3: printing the video

 3a) go to [strauh.al/scripts](https://strauh.al/scripts) and download the “layout.py” script

 3b) put the layout.py script in the folder of your computer that you want to print videos in

 3c) we will have to get our hands dirty with python code. however, the only lines of code you will need to change are:

 images_per_row = (whatever value you want, bigger values create larger images but less texture)
 images_per_column = copy and paste the value above into this field

 folder_path = "the_name_of_your_folder” (use the name of your folder that contains all of the tiff files that you exported earlier in Adobe After Effects)

 3d) run the python script in Terminal by typing in

 python3 layout.py

 3e) this python file should create a grid image inside the folder alongside your frames from After Effects. It will have the name “grid_image_1.jpg” or something like that

 3f) open the grid image and print it using ctrl - P or cmd - P. Check any options regarding if it is in color or black and white. Also make sure that it scales to the edges of the page and that it didn’t automatically rotate on its side

## step 4: scanning the print

 4a) open your scanning application of choice (it might be epson scan or you may have to go to system preferences and click on “printers and scanners”)

 4b) do an overview scan

 4c) select the area of your grid image using the marquee tool

 4d) select the scanning dpi (a smaller value will give you a pixelated image and a larger value will give you a sharper image; however larger values create tiff files that take up more space on your computer)

 4e) you want to have this scan saved as a “.tiff” file and you want to save it somewhere on your computer that will be easy to find

 4f) scan the image by pressing the scan button

## step 5: preparing the scan

 5a) open the scanned print in photoshop. we’ll have to clean it up before we turn it into a video

 5b) change the canvas size so that it’s a perfect square (the width and height have to be the same). you can get to this menu by pressing option-cmd-c

 5c) put the image in transform mode by pressing cmd-t. we need to stretch the edges of the image to the edges of the photoshop canvas.

 5d) hold the command or control key on your computer to skew the image towards the edges of the canvas (use puppet warp as needed to further fit the image to the canvas)

 5e) save the image by pressing cmd s. a dialogue will pop up asking us about tiff options. click on discard layers (to save computer space)

## step 6: turning the scan into a video

 6a) go to [strauh.al/scripts](https://strauh.al/scripts) and download the “slice.py” script

 6b) we’ll need to change 5 lines of code in this script for it to work

 square_size = min(image_width, image_height) // (PUT YOUR NUMBER HERE)
 for y in range(CHANGE THIS TO THE NUMBER ABOVE):
 for x in range(AND THIS ONE TO THE NUMBER ABOVE TOO):

 image_path = “the_name_of_your_scan.tiff”
 output_path = “the_folder_where_your_scan_will_be_sliced_into_frames” (create a new folder where your sliced frames will go)

 6c) run the python script in terminal by typing in

 python3 slice.py

## step 7: working with video

 7a) drop the folder containing the sliced print frames into Adobe After Effects

 7b) if a video does not immediately appear, drag the folder from the project window into the timeline

 7c) that’s it! if you see a video print appear, that means you’ve done everything correctly; congratulations on becoming a video printmaker

## step 8: send me your work

 8a) you’re probably one of thew few people in the world (in 2024) that is now printing videos. the only other person that comes to mind is [Julia Schmiautz](https://juliaschimautz.com) and [Daniel Savage](https://somethingsavage.com) (their work is phenomenal, check them out asap)

 8b) send me your new creation at [ernest@strauh.al](mailto:ernest@strauh.al) (don’t worry about spamming me, I’d rather see new artworks than marketing emails)

 8c) feel free to share this file with your friends; if you’re inclined to make a donation, my paypal is [paypal.me/estrauhal](https://paypal.me/estrauhal), if not, no worries

## Related Local Pages

- None yet

<!-- vault-crosslinks:start -->
## Discovered Connections

- [[knowledge/wiki/maps/Map - ChatGPT Conversations|Map - ChatGPT Conversations]] — named in this note
- [[knowledge/wiki/maps/Map - Timeline|Map - Timeline]] — named in this note
- [[knowledge/wiki/pages/scripts|scripts]] — named in this note
- [[knowledge/wiki/pages/disclaimer|disclaimer]] — named in this note
- [[knowledge/wiki/works/Video Portraiture|Video Portraiture]] — shared language: video, frames, photoshop
- [[knowledge/wiki/books/timothy-leary-what-does-woman-want|What Does WoMan Want]] — shared language: want
- [[knowledge/wiki/books/rudolf-arnheim-arnheim-rudolf-visual-thinking-35th-anniversary-printing|Visual thinking 35th anniversary printing]] — shared language: printing
- [[knowledge/wiki/books/machine-learning-mastery-jason-brownlee-deep-learning-with-python-theano-tensorflow-keras-develop-deep-learning-models-on-theano-and-tensorf|Deep Learning with Python (Theano, TensorFlow, Keras) Develop Deep Learning Models on Theano and TensorFlow Using Keras]] — shared language: python, using
<!-- vault-crosslinks:end -->
