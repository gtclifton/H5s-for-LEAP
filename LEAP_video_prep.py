import numpy as np
import cv2 as cv
from clize import run
import h5py

"""
    Remove background from image and prepare to become an .h5 for use with LEAP.


    make_h5_video(raw_vid_path, save_path, *, verbose = True, remove_bkg = True, invert = True,
                  cutoff= 5, frame_range = None, bkg_method ='div', bkg_sep = 50)\


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


    example usage from terminal:
    python3 "/home/path_to_folder/LEAP_video_prep.py" "/path_to_video.mp4" "/path_to_savefolder/Test.h5" --remove-bkg=False

"""




def load_video(raw_video_path, frame_range, verbose):
    """
    Independent of the frame range loaded, background has to be computed over total video or else can run into
    tracking problems
    """
    vid = cv.VideoCapture(raw_video_path)
    Height = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT))
    Width = int(vid.get(cv.CAP_PROP_FRAME_WIDTH))
    NumFrames = int(vid.get(cv.CAP_PROP_FRAME_COUNT))
    if not (NumFrames > 0):
        raise IOError('Codec issue: cannot read number of frames.')

    # restrict to desired range of frames
    if frame_range is None:
        frame_range = (0, int(NumFrames))
    else:
        # check doesn't exceed number of frames
        if frame_range[0] + frame_range[1] > NumFrames:
            frame_range = (int(frame_range[0]), int(NumFrames - frame_range[0]))

    # initialize blank frames
    frames = np.zeros((frame_range[1], Height, Width), np.uint8)

    # set the first frame to read in
    vid.set(cv.CAP_PROP_POS_FRAMES, 0)
    for kk in range(frame_range[0]):
        tru, ret = self.vid.read(1)
    # vid.set(cv.CAP_PROP_POS_FRAMES, frame) # this way of setting the frame doesn't work on all cv versions

    # read in all frames
    for kk in range(frame_range[1]):
        tru, ret = vid.read(1)

        # check if video frames are being loaded
        if not tru:
            raise IOError('Codec issue: cannot load frames.')

        frames[kk, :, :] = ret[:, :, 0]  # assumes loading color

        if ((kk % 100) == 0) and verbose:
            print(kk)

    return frames, NumFrames, frame_range, vid



def remove_background(raw_video_path, frame_range, bkg_method, bkg_sep, verbose):

    # load in video, get video features
    frames, NumFrames, frame_range, vid = load_video(raw_video_path, frame_range, verbose)

    # if all frames loaded, do as normal
    if frame_range[1] == NumFrames:
        background = np.float32(np.median(frames[0::bkg_sep,:,:], axis = 0))
        if verbose:
            print('all_loaded!')
    else: # still use full video for background, not just desired output range
        background = []
        for kk in range(0, NumFrames, bkg_sep):
            vid.set(cv.CAP_PROP_POS_FRAMES, kk)
            tru, ret = vid.read(1)

            # check if video frames are being loaded
            if not tru:
                raise IOError('Codec issue: cannot load frames.')

            background.append(ret[:,:,0])  # assumes loading color

        background = np.array(background, dtype='float32')
        background = np.float32(np.median(background, axis=0))

    # add a small number to background to not have divide by zeros for division
    background = background + np.float32(1E-6)
    if verbose:
        print('Background calculated')

    if bkg_method == 'div':
        norm_bkg = np.mean(background[:])  # normalize for mean intensity of image
        # norm_frm = np.mean(frames, axis=(1,2)) # normalize for mean intensity of current frame. For flicker
        frames_normed = (frames / norm_bkg) / (background / norm_bkg)  # broadcasting

    elif bkg_method == 'sub':
        raise IOError('Code does not currently support background subtraction, only division')
    else:
        raise IOError('Background divsion/subtraction method not recognized. Use div.')

    if verbose:
        print('Background removed')

    return frames_normed


def augment_contrast(frames, invert, cutoff, verbose):

    # center around 0 (neg = darker than background, pos = lighter than background)
    frames = frames-1

    # if there is a light backgroud, invert images
    if invert:
        frames = -1*frames
        if verbose:
            print('Inverted frames')

    # find max pixel value for each frame
    max_pixel_vals = frames.max(1).max(1)

    # divide by max so that all darker than background pixels are from -1 to 0 and lighter pixels are from 0 to 1
    frames_maxone = frames / max_pixel_vals[:,None,None]
    if frames_maxone.max(1).max(1).max(0) > 1:
        raise IOError('Error in normalized image. Did you background divide?')

    # shift pixel values to determine how dark the background should be
    frames_contrast = (255-cutoff)*frames_maxone + cutoff
    frames_contrast[frames_contrast<0]=0

    return frames_contrast


def save_as_h5(frames_contrast, save_path, verbose):

    # convert frames to int
    frames_tosave = frames_contrast.astype(np.uint8)

    # make np array the right shape to become an .h5
    h5_tosave = np.array([frames_tosave])
    h5_tosave = np.swapaxes(np.swapaxes(h5_tosave,0,1),2,3)

    # save it in desired location
    hf = h5py.File(save_path, 'w')
    hf.create_dataset('box', data=h5_tosave)
    hf.close()

    if verbose:
        print('Saved as .h5')

    return


def make_h5_video(raw_vid_path, save_path, *, verbose = True, remove_bkg = True, invert = True,
                  cutoff= 5, frame_range = None, bkg_method ='div', bkg_sep = 50):

    if verbose:
        print("analyzing video:", raw_vid_path)

    # either remove background or load video with background already removed
    if remove_bkg:
        frames_normed = remove_background(raw_vid_path, frame_range, bkg_method, bkg_sep, verbose)
    else:
        frames_normed = load_video(raw_vid_path, frame_range, verbose)[0]

    # alter gain of image to highlight subject vs. background
    frames_contrast = augment_contrast(frames_normed, invert, cutoff, verbose)

    # save image as a hdf5
    save_as_h5(frames_contrast, save_path, verbose)

    print('went through function')
    return


if __name__ == "__main__":
    run(make_h5_video)