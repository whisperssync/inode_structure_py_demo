
from volume import * 
from subprocess import call

class TinyDOS:	
	def __init__(self):
		self.volume = None
		self.connected = False
		
	def prompt(self):
		while True:
			try:
				command = input("").strip()
				if command:
					self.proceed_command(command)
			except EOFError:
				print("All tests passed. Quitting TinyDOS")
				quit()

	def proceed_command(self,command):
		tokens = command.split()
		initial_commands = ["format","reconnect"]
		exit_commands = ["quit"]
		if self.connected and tokens[0] in initial_commands:
			print("Invalid command. Already connected to a drive.")
			return
		if not (self.connected or tokens[0] in initial_commands):
			print("Invalid command. Connect to a drive first.")
			return	

		if tokens[0] == "format" and len(tokens) == 2:
			self.volume = Volume(tokens[1])
			self.volume.volume_format()
		elif tokens[0] == "ls" and len(tokens) == 2:
			self.volume.list_file(tokens[1])
		elif tokens[0] == "mkfile" and len(tokens) == 2:
			self.volume.make_file(tokens[1])
		elif tokens[0] == "mkdir" and len(tokens) == 2:
			self.volume.make_dir(tokens[1])
		elif tokens[0] == "append" and len(tokens) == 3:
			string = (" ".join(tokens[2:])).strip('"')
			self.volume.append_to_file(tokens[1], string)
		elif tokens[0] == "print" and len(tokens) == 2:
			print(self.volume.show_file(tokens[1]))
		elif tokens[0] == "delfile" and len(tokens) == 2:
			self.volume.delete_file(tokens[1])
		elif tokens[0] == "deldir" and len(tokens) == 2:
			self.volume.delete_dir(tokens[1])
		elif tokens[0] == "quit" and len(tokens) == 1:
			self.volume.disconnect_drive()
			quit()
		elif tokens[0] == "reconnect" and len(tokens) == 2:
			self.volume = Volume(tokens[1])
			origin = self.volume.reconnect_drive()
		else:
			print("Invalid command.")
			return
		if tokens[0] in initial_commands:
			self.connected = True	
		if tokens[0] in exit_commands:
			self.connected = False
	
			

if __name__ == "__main__":
	tinydos = TinyDOS()
	tinydos.prompt()