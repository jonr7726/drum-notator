from mingus.extra.lilypond import to_pdf
#from mingus.extra.lilypond import to_png

path = input("Enter file path: ").split('.')[0]

text_file = open(path + ".txt", "r")
notation_string = text_file.read()

# Write notation to pdf
to_pdf(notation_string, path)
#to_png(notation_string, path)