from mingus.extra.lilypond import to_pdf, to_png
import os

path = input("Enter file path: ")

if len(path.split(".")) > 1:
	if path.split(".")[1] == "txt":
		text_file = open(path, "r")
		notation_string = text_file.read()
		text_file.close()

		# Write notation to pdf
		to_pdf(notation_string, path.split(".")[0])
		to_png(notation_string, path.split(".")[0])
else:
	# Entered directory
	for file in os.listdir(path):
		if len(file.split(".")) > 1:
			if file.split(".")[1] == "txt":
				text_file = open(path + file, "r")
				notation_string = text_file.read()
				text_file.close()

				# Write notation to pdf
				to_pdf(notation_string, path + file.split(".")[0])
				to_png(notation_string, path + file.split(".")[0])