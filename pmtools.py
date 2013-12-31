import os
import glob

MAX_DEPTH_RECUR = 50
''' The maximum depth to reach while recursively exploring sub folders'''


def get_files_from_dir(path, recursive=True, depth=0, file_ext='.py'):
    '''Retrieve the list of files from a folder.

    @param path: file or directory where to search files
    @param recursive: if True will search also sub-directories
    @param depth: if explore recursively, the depth of sub directories to follow
    @param file_ext: the files extension to get. Default is '.py'
    @return: the file list retrieved. if the input is a file then a one element list.

    '''
    file_list = []
    if os.path.isfile(path):
        return [path]
    if path[-1] != os.sep:
        path = path + os.sep
    for f in glob.glob(path + "*"):
        if os.path.isdir(f):
            if depth < MAX_DEPTH_RECUR:  # avoid recursive loop
                file_list.extend(get_files_from_dir(f, recursive, depth + 1))
            else:
                continue
        elif f.endswith(file_ext):
            file_list.append(f)
    return file_list
