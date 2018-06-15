# H5s-for-LEAP
Python function to create an .h5 file compatible with LEAP deep learning analysis.

Remove background from image and prepare to become an .h5 for use with LEAP (https://github.com/talmo/leap)





MAIN FUNCTION:
make_h5_video(raw_vid_path, save_path, *, verbose = True, remove_bkg = True, invert = True,
              cutoff= 5, frame_range = None, bkg_method ='div', bkg_sep = 50)\


INPUT PARAMETERS:

:param raw_vid_path: path to video file you would like to analyze
:param save_path: where would you like to save the .h5?
:param verbose: if True, prints updates about the process
:param remove_bkg: TRUE = calculates and divides image by background. If FALSE, make sure you input a video where
    pixel value of 1 = same as background value
:param invert: list TRUE if your subject/background is dark/light. list False if subject/backfround is light/dark
:param frame_range: defines which frames you would like to analyze
:param cutoff: this value defines the pixel value for when the raw video pixel value = background. Shift this to
    make your video contrast look great.
:param bkg_method: currently only background division ('div') is functional. leaving this parameter in for future
    expansion to include background subtraction
:param bkg_sep: the separation between frames pulled from the video to determine the background pixel values



EXAMPLE USAGE FROM TERMINAL:

python3 "/home/path_to_folder/LEAP_video_prep.py" "/path_to_video.mp4" "/path_to_savefolder/Test.h5" --remove-bkg=False
