
import drive 

class Volume:
    USED_BIT = "+"
    UNUSED_BIT = "-"
    ENTRY_INFO_LENGTH = 64
    
    def __init__(self,name):
        self.drive = drive.Drive(name)
        self.drive_structure = ["",[]] # a list to store the files' hierachy
        self.entries = {"":EntryInfo(EntryInfo.DIR, "",[0])} # a dictionary to store all the EntryInfos.
        self.blocks = [Volume.USED_BIT]+[Volume.UNUSED_BIT]*(self.drive.DRIVE_SIZE -1) # a list to track all blocks in drive

         
    def volume_format(self):
        self.drive.format()
        # format block 0
        bitmap = "".join(self.blocks)
        entries_num = (self.drive.BLK_SIZE - len(bitmap))//Volume.ENTRY_INFO_LENGTH
        entries = ""
        for i in range(entries_num):
            entry = EntryInfo(EntryInfo.FILE,"",[])  
            entries += str(entry)
        data = bitmap + entries
        self.drive.write_block(0, data)
            
    def make_file(self,file_name):
        new_file_entry = EntryInfo(EntryInfo.FILE, file_name,[])
        self.put_entry(new_file_entry) # find its postion in the drive's file hierachy
        self.add_to_dir(new_file_entry) # update its parent dir
        self.entries[file_name] = new_file_entry
    
    def append_to_file(self, file_name, content):
        try:
            file_entry = self.entries[file_name]
        except:
            raise Exception("No such file.")
            
        # find which block to start writing in    
        if file_entry.blocks == []:
            target_block = self.next_empty_block()
        else:    
            target_block = file_entry.blocks[-1]
        # read current valid data, append new content
        valid_data_size = file_entry.size % self.drive.BLK_SIZE
        data = self.drive.read_block(target_block)[:valid_data_size]
        data += content
        file_size_limit = self.drive.BLK_SIZE * 12
        if len(data) > file_size_limit:
            raise Exception("File size beyond limit ",file_size_limit)
        file_entry.size += len(content)    
        # extract data for one block, write back, repeat
        while data:
            try:
                data_to_write = data[:self.drive.BLK_SIZE]
            except:
                data_to_write = data
            self.set_bitmap(target_block, Volume.USED_BIT)    
            self.drive.write_block(target_block, "{: <{width}}".format(data_to_write,width = self.drive.BLK_SIZE))
            self.entries[file_entry.name].blocks.append(target_block)
            target_block += 1            
            try:
                data = data[self.drive.BLK_SIZE:]
            except:
                pass
        self.update_dir(file_entry)
 
    def make_dir(self, dir_name):
        new_dir_entry = EntryInfo(EntryInfo.DIR, dir_name,[])
        self.put_entry(new_dir_entry)
        self.add_to_dir(new_dir_entry)
        self.entries[dir_name] = new_dir_entry
                    
    def list_file(self,dir_name):
        print("Directory: " + dir_name)
        print("Name     Type Size")
        print("----     ---- ----")
        
        steps, end_dir, condition = self.crawl_path(self.parse_path(dir_name))
        if steps == []:
            target_dir = self.drive_structure[1]
        else:
            target_dir = end_dir[steps[-1]][1]
        for each_entry in target_dir:
            entry_name = dir_name.rstrip("/") + "/" + each_entry[0]
            entry = self.entries[entry_name]
            print("{:<9}".format(entry.name_in_dir) + "{:>4}".format(entry.filetype) + " " +"{:>4}".format(entry.size))
     
    def show_file(self, file_name):
        text = ""
        try:
            entry = self.entries[file_name]
        except:
            raise Exception("No such file.")
        for each_block in entry.blocks:
            text += self.drive.read_block(each_block)
        return text.rstrip()
                  
    def delete_file(self, file_name):
        try:
            file_entry = self.entries[file_name]
        except:
            raise Exception("No such file.")
        self.remove_entry(file_entry)    
        self.update_dir(file_entry, delete = True)
        self.clear_entry_block(file_entry)
        self.entries.__delitem__(file_name)
    
    def delete_dir(self, dir_name):
        try:
            dir_entry = self.entries[dir_name]
        except:
            raise Exception("No such directory.")
        for each_block in dir_entry.blocks:
            data = self.drive.read_block(each_block)
            if not (data.strip() == "" or data == str(EntryInfo(EntryInfo.FILE,"",[])) * (self.drive.BLK_SIZE//Volume.ENTRY_INFO_LENGTH)): 
                raise Exception("Can't delete non-empty directory.")       
        self.remove_entry(dir_entry)
        self.update_dir(dir_entry, delete = True)
        self.clear_entry_block(dir_entry)
        self.entries.__delitem__(dir_name)    
    
    def disconnect_drive(self):
        self.drive.disconnect()
    
    def reconnect_drive(self):
        self.drive.reconnect()
        self.blocks = list(self.drive.read_block(0)[:self.drive.DRIVE_SIZE])
        self.build_drive_structure()
       
    def clear_entry_block(self, entry):
        for each_block in entry.blocks:
            self.drive.write_block(each_block, " " * self.drive.BLK_SIZE)
            self.set_bitmap(each_block, Volume.UNUSED_BIT)       
        entry.blocks = []
        entry.size = 0
                
    def crawl_path(self, path):
        # crawl the path from root directory to the end if possible, return (steps, entries contained at the stop directory, condition code) 
        # healper function called to locate entry the drive structure.
        if not path[0] == "":
            raise Exception("Start the full name with /.")
        path_levels = len(path)
        level = 1
        current_dir = self.drive_structure[1] # start from root directory
        crawl_step = [] 
        while True:
            is_end = (level == path_levels - 1)
            entry_in_path = path[level]
            current_dir_entry_names = [each_entry[0] for each_entry in current_dir]
            if not is_end: # crawl along the path
                found_path = False
                if entry_in_path in current_dir_entry_names:
                    found = True
                    idx = current_dir_entry_names.index(entry_in_path)
                    crawl_step.append(idx)
                    level += 1
                    current_dir = current_dir[idx][1]
                    continue
                else:
                    condition = 3 # condition 3: can't find path, stop in middle
                    break 
            else: # is_end = True, reach path end
                if entry_in_path in current_dir_entry_names:
                    idx = current_dir_entry_names.index(entry_in_path)
                    crawl_step.append(idx)
                    condition = 1 # condition 1: crawl to end and find the entry
                else:
                    condition = 2 # condition 2: crawl to end and can't find the entry 
                break       
        return crawl_step, current_dir, condition
                
    def put_entry(self, entry):
        # put entry in drive structure
        path = self.parse_path(entry.name)
        steps, end_dir, condition = self.crawl_path(path)
        if condition == 1:
            raise Exception("Already exists. Please change a name.")
        elif condition == 3:
            raise Exception("Can't store the data. Invalid path.")
        if len(path) == 2: #root dir
            if len(end_dir) == (self.drive.BLK_SIZE - self.drive.DRIVE_SIZE)//Volume.ENTRY_INFO_LENGTH:
               raise Exception("Directory is full. Can't put in more entry.") 
        else:
            if len(end_dir) == self.drive.BLK_SIZE//Volume.ENTRY_INFO_LENGTH * 12:
                raise Exception("Directory is full. Can't put in more entry.")    
        if not entry.is_file():
            end_dir.append([entry.name_in_dir,[]])
        else:
            end_dir.append([entry.name_in_dir])      
    
    def remove_entry(self, entry):
        steps, end_dir, condition = self.crawl_path(self.parse_path(entry.name))
        end_dir.pop(steps[-1])  
              
    def initialize_dir(self, block):
        # fill new empty dir with f:  000000000...."
        self.drive.write_block(block,str(EntryInfo(EntryInfo.FILE, "", [])) * (self.drive.BLK_SIZE//Volume.ENTRY_INFO_LENGTH))
        
    def parse_path(self, entry_name):
        return entry_name.split("/")
          
    def next_empty_block(self):
        try:
            return self.blocks.index(Volume.UNUSED_BIT)
        except ValueError:
            raise Exception("Failed. No empty space for new data.")
    
    def parent_dir(self, entry):
        entry_path = self.parse_path(entry.name)            
        for each_entry_name in self.entries.keys():
            if each_entry_name == "/".join(entry_path[:len(entry_path)-1]).lstrip(): # find the dir that contains the para entry
                return self.entries[each_entry_name]
            
    def find_dir_space(self, dir_entry):
        # find empty entry space for new entry in a dir
        for each_block in dir_entry.blocks:
            data = self.drive.read_block(each_block)
            if data.find(str(EntryInfo(EntryInfo.FILE, "",[]))) != -1:
                return each_block
        return False        
    
    def add_to_dir(self,entry):
        # udpate entry's parent dir after add new entry, allocate new block to parent dir if needed.
        parent_dir = self.parent_dir(entry)
        if parent_dir.blocks != [0] and self.find_dir_space(parent_dir) is False: #need new block to dir
            target_block = self.next_empty_block()
            self.initialize_dir(target_block)
            self.set_bitmap(target_block, Volume.USED_BIT)
            parent_dir.blocks.append(target_block)
            parent_dir.size += self.drive.BLK_SIZE
            if parent_dir.blocks != [0]:
                self.update_dir(parent_dir)
        else:
            target_block = self.find_dir_space(parent_dir)
        data = self.drive.read_block(target_block)
        new_data = data.replace(str(EntryInfo(EntryInfo.FILE, "",[])), str(entry),1)
        self.drive.write_block(target_block, new_data)

    def update_dir(self, entry, delete = False):
        # update parent dir after modify/delete entry, revoke parent dir's block if it's empty afterwards
        parent_dir = self.parent_dir(entry)
        for each_block in parent_dir.blocks:
            if str(entry)[:11] in self.drive.read_block(each_block):
                target_block = each_block
        data = self.drive.read_block(target_block)      
        pos = data.index(str(entry)[:11])
        if not delete:
            new_data = data[:pos] + str(entry) + data[pos + Volume.ENTRY_INFO_LENGTH:]
        else:
            new_data  = data[:pos] + str(EntryInfo(EntryInfo.FILE, "", [])) + data[pos + Volume.ENTRY_INFO_LENGTH:]
            empty_parent_dir = True
            for each_block in parent_dir.blocks:
                if self.drive.read_block(each_block) != str(EntryInfo(EntryInfo.FILE, "", [])) * 8:
                    empty_parent_dir = False
            if empty_parent_dir: # if the parent dir becomes empty after this file deletion, revoke its block
                self.clear_entry_block(parent_dir)
                self.update_dir(parent_dir, delete = True) 
        self.drive.write_block(target_block, new_data)
        
    def set_bitmap(self,bitnum, value):
        self.blocks[bitnum] = value
        block0_data = self.drive.read_block(0)
        bitmap = block0_data[:self.drive.DRIVE_SIZE]
        bitmap = bitmap[:bitnum] + value + bitmap[bitnum + 1:]
        self.drive.write_block(0, bitmap + block0_data[self.drive.DRIVE_SIZE:])    
    
    def extract_entry_infos(self, dir_block):
        # extract entry info from a block's data
        result = []
        data  = self.drive.read_block(dir_block)
        if dir_block == 0:
            count = self.drive.DRIVE_SIZE
        else:
            count = 0
        while count < self.drive.BLK_SIZE:
            entry_info = data[count : count + Volume.ENTRY_INFO_LENGTH]
            result.append(entry_info) 
            count += Volume.ENTRY_INFO_LENGTH       
        return result           
        
    def build_drive_structure(self):
        # recover drive structure after reconnect
        self.drive_structure = self.build_entry_structure(EntryInfo(EntryInfo.DIR, "", [0], self.drive.BLK_SIZE))
        
    def build_entry_structure(self, entry): 
        #recursivly build each child dir's structure
        entry_structure = [entry.name_in_dir,[]]
        if not entry.is_file() and not entry.is_empty(): # if entry is a dir and not holds data, aka. not a leave level entry
            dir_entries = []
            for each_block in entry.blocks:
                dir_entries += self.extract_entry_infos(each_block)
            for entry_info in dir_entries:
                paras = self.parse_entry_info(entry_info)
                new_entry = EntryInfo(paras["type"], entry.name+ "/" + paras["name"].strip(), paras["blocks"], paras["size"])
                self.entries[new_entry.name] = new_entry
                new_entry_structure = self.build_entry_structure(new_entry)
                if new_entry_structure[0]:
                    entry_structure[1].append(new_entry_structure)
        else:
            if entry.is_file():
                return [entry.name_in_dir]
            else:
                return [entry.name_in_dir,[]]
        return entry_structure        
      
    def parse_entry_info(self,entry_info):
        # parse entryinfo object for entry's information
        block_string = entry_info[16:]
        blocks = []
        for each_block_string in block_string.split(" "):
            if each_block_string.lstrip("0").strip(" "):
                blocks.append(int(each_block_string))
        info = {
        "type": entry_info[:2],
        "name": entry_info[2:11],
        "blocks": blocks ,
        "size": entry_info[11:15],
        }
        return info          

class EntryInfo:
    FILE = "f:"
    DIR = "d:"
    def __init__(self,filetype, name, blocks, size = 0):
        self.filetype = filetype
        self.name = name
        self.blocks = blocks
        self.size = size
        self.name_in_dir = self.name.split("/")[-1]
    def __str__(self):
        result = self.filetype + "{:<8}".format(self.name_in_dir)+" "+"{:0>4}".format(self.size)+":"+ self.block_graph()
        return result
    
    def block_graph(self):
        # byte 16-63 of the entry, representing the blocks the entry uses
        graph = ""
        for block_used in self.blocks:
            graph += "{:0>3}".format(block_used)+" "
        graph += "000 "* ((48 - len(graph))//4)
        return graph
    def is_file(self): # return false if it's dir
        return self.filetype == EntryInfo.FILE
    def is_empty(self): # return if the dir entry is emptry
        return self.blocks ==[]

