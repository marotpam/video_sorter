import os
import os.path as path
from ConfigParserAdapter import ConfigParserAdapter
import time
import pprint
import guessit
import shutil
import sys
import argparse
from opensubtitles import search_subtitles

ORIGIN_DIRECTORY = #the root folder to start looking for movies
TV_SHOWS_ROOT    = #the root folder where tv shows are stored
MOVIES_ROOT      = #the root folder where movies are stored

video_extensions = ["mkv", "mp4", "avi", "wmv"]
hearing_impaired_prefixes = ['[', '(']

"""Gets the extension of a given file by its filename"""
def get_extension( filename ):
    return filename[filename.rfind(".")+1:]

"""Returns true if the given filename has a video extension"""
def is_video_file( filename ):
    return not 'sample' in filename and get_extension(filename) in video_extensions

"""Gets a list of all the video files located in a given folder (and its sons)"""
def get_videos_in_dir_recursive( root, recursion_level = 0 ):
    if recursion_level == 5:
        return []
    video_files = sorted( [path.join(root,f) for f in os.listdir( root ) if path.isfile( path.join( root,f ) ) and is_video_file(f)] )
    directories = sorted( [path.join( root,f ) for f in os.listdir( root ) if path.isdir( path.join( root,f ) )] )
    for dir in directories:
        video_files = video_files + get_videos_in_dir_recursive(path.join( root,dir ), recursion_level + 1 )
    return video_files

"""Removes all lines containing descriptions for hearing impared and
   the names of characters talking from the subtitles file passed as a parameter"""
def clean_subtitles(subs_file):
    lines_without_sounds = [line.strip() for line in open( subs_file ) if line[:1] not in hearing_impaired_prefixes]

    clean_lines = []
    for line in lines_without_sounds:
        line_to_append = line
        if '-->' not in line:
            #dialog line
            separator_index = line.find(':')
            if separator_index >= 0:
                #contains a :
                last_space = line[:separator_index].rfind(' ')
                if not line[last_space+1:separator_index].isdigit():
                    # : is not the separator of an hour
                    line_to_append = line[separator_index+1:]

        clean_lines.append(line_to_append)

    output_file = open( subs_file, 'w' )
    output_file.write( "\n".join( clean_lines ) )

"""Moves the parent folder of a video file to the movies_folder in test.cfg"""
def move_to_movie_folder( video_file ):
    dest_dir = MOVIES_ROOT
    move_directory( path.dirname( video_file ), dest_dir )

"""Moves the parent folder of a video file to the shows_folder in test.cfg"""
def move_to_show_folder( video_file, video_info ):
    dest_dir = TV_SHOWS_ROOT + video_info['series']
    move_directory( path.dirname( video_file ), dest_dir )

"""Moves the file stored in origin_directory to destination_directory.
   overwrite parameter specifies whether a file in the destination_directory with
   the same name as the file origin_directory should be overwritten or not"""
def move_directory( origin_directory, destination_directory, overwrite = False ):
    exists_in_destination = path.exists( path.join( destination_directory, path.basename( origin_directory ) ) )
    if path.exists(origin_directory) and ( not exists_in_destination or overwrite ):
        print "moving " + origin_directory + " to " + destination_directory + "...\n"
        shutil.move( origin_directory, destination_directory )

"""Returns the subtitles filename of a given videofile, or an empty string if there are no subtitles"""
def get_subtitles_filename(video_file):
    return video_file[:video_file.rfind('.')]+'.srt'

def video_has_subtitles(video_file):
    expected_subtitles_filename = get_subtitles_filename(video_file)
    return path.exists(expected_subtitles_filename)

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def is_in_own_subdirectory(video_file):
    parent_file = path.abspath(path.join(video_file, os.pardir))
    parent_file_size = get_size(parent_file)
    video_file_size = path.getsize(video_file)
    video_size_perc_in_folder = str(float(video_file_size)/float(parent_file_size))
    return video_size_perc_in_folder > 0.95

video_files = [f for f in get_videos_in_dir_recursive( ORIGIN_DIRECTORY )]
only_subtitles = False
if ( len(sys.argv) > 1 and sys.argv[1] == "-s" ):
    only_subtitles = True

for video_file in video_files:
    print 'next video file ' + str(video_file)

    if not video_has_subtitles(video_file):
        search_subtitles([video_file])
    if video_has_subtitles(video_file):
        clean_subtitles(get_subtitles_filename(video_file))
    if only_subtitles:
        continue

    video_info = guessit.guess_video_info( video_file )
    if ( video_info['type'] == 'movie' ):
        move_to_movie_folder( video_file )
    elif ( video_info['type'] == 'episode' ):
        move_to_show_folder( video_file, video_info )
