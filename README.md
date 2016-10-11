# inode_structure_py_demo
A simple demonstration of inode pointer structure 

Includes three python files:
###tinyDOS.py 
The user interface that accepts the following commands to operate on the file system
- `format volumeName`formats the virtual disk file for further commands
- `reconnect volumeName` reconnects to the VDF to continue operating on it
- `ls fullDirectoryPathname` lists entries of a diretor
- `mkfile fullFilePathname` makes new file. No block is allocated at this point 
- `mkdir fullDirectoryPathname` makes new directory. New directories are initialised with empty file entries
- `append fullFilePathname data` writes to file entries
- `print fullFilePathname` prints content of a file entry to cosole
- `delfile fullFilePathname` deletes file entries
- `deldir fullDirectoryPathname` deletes empty directory entries
- `quit` disconnect the VDF and quit the tinyDOS

###volume.py
In reality, a computer can only make sense of data stored in a drive with the help of volume meta data.

###drive.py
Created by Robert. It provides interface to read from/write to the VDF

USAGE:
1. `python3 tinyDOS.py` to start the console
2. `format drivename` to mount a drive
3. `watch head drivename` to inspect the drive's inode instructure
