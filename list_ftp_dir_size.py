# -*- coding: utf-8 -*-

# A simple Python script for working out the total size of a connected directory
# via FTP.
# @author: Darren Vong

from ftplib import FTP, error_perm
import os
import sys


def calculate_total_size(ftp, dir_name, parent, max_depth=5, unexplored_size=50000):
    """Recursively walks through a directory to determine its total size,
    in bytes, of the directory dir_name.
    
    Other params:
    @param ftp - the FTP connection resource handle
    @param dir_name - the name/path to the subdirectory, relative to parent.
    This can be empty if function is initially called at parent.
    @param parent - the parent directory the search begins from.
    @keyword max_depth - the maximum depth of subdirectories (counting from the
    original parent level) to walk through in a given "branch". In other words,
    if the level of the subdirectory is greater than this, the function will
    not walk/recurse into further subdirectories. The default value for this is 5.
    @keyword unexplored_size - the "estimate" size to assign to a folder not
    explored due to max_depth being reached. Default is 50000 bytes.


    Return: the (approximate, in cases where unorthodox files' size can't be
    determined easily) total bytes of the directory dir_name.
    """
    
    total_size = 0
    if dir_name != "":
        parent = parent + "/" + dir_name
        if max_depth != 0:
            ftp.cwd(dir_name)
        else:
            return unexplored_size
    
    # List of folders and files as string name
    black_list = [".cpanel"]
    valid_listings = [l for l in ftp.nlst() if l not in [".", ".."]]
    for content in valid_listings:
        if content in black_list: # Cheap filter to skip if in blacklist
            continue
        else:
            file_check_result = is_file(ftp, content)
            if file_check_result == 1:
                total_size += ftp.size(content)
            elif file_check_result == 0: # Folder
                try:
                    total_size += calculate_total_size(ftp, content, parent, max_depth-1)
                    ftp.cwd(parent)
                except:
                    # The problematic file
                    print "The problematic file is", os.path.join(parent, content)
                    continue
            else: # Some unorthodox/unknown/undiscoverable directory
                continue
    
    return total_size

def directory_size(ftp, subdir_listing, parent, max_depth=5, unexplored_size=50000):
    """Useful auxiliary function to calculate_total_size to see the script's
    progress for large directories with lots of first-level subdirectories.
    @param subdir_listing - the list of subdirectory names/files
    
    See calculate_total_size doc for the meaning of the other parameters.
    """
    ftp.cwd(parent)
    print "\nThe topmost parent directory is", ftp.pwd()
    
    overall_size = 0
    files, subdirs = sanitise_listing(ftp, subdir_listing)
    for f in files:
        overall_size += ftp.size(f)
    
    for subdir in subdirs:
        size = calculate_total_size(ftp, subdir, parent)
        print subdir, "size:", size, "bytes"
        overall_size += size
        ftp.cwd(parent) # Resets back to original parent dir
    
    return overall_size

def sanitise_listing(ftp, listing):
    """Sanitise a list of directory listings and return them as a pair of separate lists,
    one containing files only and one containing purely directories.
    @param ftp - the FTP connection resource handle
    @param listing: the directory listing to sanitise/filter through
    
    @return: a tuple (pair) of lists with the left list being the file names and right
    list being the directory names.
    """
    
    file_names = [f for f in listing if is_file(ftp, f) == 1]
    directories = [d for d in listing if d not in file_names]
    
    return file_names, directories

def is_file(ftp, name):
    """Determines whether :name is an 'ordinary' file or not
    @return: 1 if it is an ordinary file, 0 if it is a folder, -1 otherwise.
    """

    try: # File size can be determined, so must be an ordinary file
        ftp.size(name)
        return 1
    except error_perm as e: # Folder or other unorthodox files
        folder_msg = "I can only retrieve regular files"
        if folder_msg in e.message:
            return 0
        else:
            return -1

def connect(host, username, password):
    """Returns a FTP connection to the host.
    @param host - the name of the host to connect to
    @param username - the account's user name to make the FTP connection from
    @param password - the password for the user
    """
    
    ftp = FTP(host)
    ftp.login(username, password)
    print "\n", ftp.getwelcome()
    
    return ftp

if __name__ == '__main__':
    try:
        # replace HOST_NAME, USER_NAME, PASSWORD with the relevant credentials
        HOST_NAME, USER_NAME, PASSWORD = (os.environ["FORGE_HOST"],
            os.environ["FORGE_NAME"], os.environ["FORGE_PASS"])
        ftp = connect(HOST_NAME, USER_NAME, PASSWORD)
        origin = "/public_html/wp-content/plugins"
        
        with open("plugins.txt", "r") as dirs:
            dir_list = [dir_name.strip() for dir_name in dirs]
        
        print directory_size(ftp, dir_list, origin), "Bytes"
        
    except IOError as e:
        print e
    except:
        print sys.exc_info()
    finally:
        ftp.close()
