# -*- coding: utf-8 -*-

# A simple Python script for working out the total size of a connected directory
# via FTP.
# @author: Darren Vong

from ftplib import FTP, error_perm
import os
import sys


def calculate_total_size(ftp, dir_name, origin):
    """Recursively walks through any directories to determine the total size,
    in bytes, of the directory dir_name.
    
    Other params:
    ftp - the FTP connection resource handle
    origin - the parent directory name, obtained by appending dir_name using
    os.path.join

    Return: the (approximate, in cases where unorthodox files' size can't be
    determined easily) total bytes of the directory dir_name.
    """

    total_size = 0
    if dir_name != "":
        ftp.cwd(dir_name)
    origin = os.path.join(origin, dir_name)
    # List of folders and files as string name
    for content in ftp.nlst()[2:]:
        # dot_index = content.find(".")
        
        if is_file(content):
            total_size += ftp.size(content)
        else: # Folder or unorthodox file
            try:
                total_size += calculate_total_size(ftp, content, origin)
                ftp.cwd(origin)
            except:
                print os.path.join(origin, content) # The problematic file
                continue
    
    return total_size

def is_file(name):
    """Determines whether :name is an 'ordinary' file or not
    @return: True if it is an ordinary file, False otherwise.
    """

    try: # File size can be determined, so must be an ordinary file
        ftp.size(name)
        return True
    except error_perm: # Folder or other unorthodox files
        return False

if __name__ == '__main__':
    try:
        # HOST_NAME, USER_NAME, PASSWORD here are placeholders. They should be
        # read in from a config file or from env vars
        HOST_NAME, USER_NAME, PASSWORD = "example.com", "bob", "password"
        ftp = FTP(HOST_NAME)
        ftp.login(USER_NAME, PASSWORD)

        print ftp.getwelcome()
        origin = "public_html/wp-content"
        ftp.cwd(origin)
        print "\n", ftp.pwd()
        
        # List of folders and files as string name
        print calculate_total_size(ftp, "", origin), "Bytes"
    except:
        print sys.exc_info()
    finally:
        ftp.close()
