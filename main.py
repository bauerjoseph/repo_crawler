# Other libraries
from pydriller import * 
import subprocess
import os

from xml.dom import minidom
from xml.parsers.expat import ExpatError

# Our imports
from config import git_repo

#### Helper functions

#Takes a file name as an input and determines if it is a source file or not
def IsSourceFile(filename):
    is_src = None
    if(filename.find(".") >= 0):
        file_extention = m.filename.split(".")[1]
        if file_extention in SRC_FILES:
            is_src = file_extention
    return is_src

# get srcML of file
def GetSRCML(source):
    result = subprocess.check_output(['srcml', source])
    return result

def GetVariableNamesFromSRCML(xml_string):
    toReturn = []

    xml = minidom.parseString(xml_string)

    unit = xml.documentElement
    declarations = unit.getElementsByTagName("decl_stmt")

    for x in declarations:
        decl = x.childNodes
        for child in decl[0].childNodes:
            if(child.nodeType != child.TEXT_NODE):
                if(child.tagName == 'name'):
                    for y in child.childNodes: # get variable name
                        if(y.nodeValue != None):
                            toReturn.append(y.nodeValue)
    return toReturn

def GetFunctionNamesFromSRCML(xml_string):
    toReturn = []

    xml = minidom.parseString(xml_string)

    unit = xml.documentElement
    functions = unit.getElementsByTagName("function")

    for func in functions:
        for child in func.childNodes:
            if(child.nodeType != child.TEXT_NODE):
                if(child.tagName == 'name'):
                    for y in child.childNodes: # get variable name
                        if(y.nodeValue != None):
                            toReturn.append(y.nodeValue)
    return toReturn

def IsCamelCase(s):
    return s != s.lower() and s != s.upper() and "_" not in s and s[0] != s[0].upper()

def IsSnakeCase(s):
    return s.find('_') > 0 and s[-1] != '_'

def CountLeadingSpaces(s):
    return len(s) - len(s.lstrip(' '))

def CountLeadingTabs(s):
    return len(s) - len(s.lstrip('\t'))

## MAIN ###

# CONSTANTS
SRC_FILES = ["c", "cpp", "cc", "cs"]

# Creating files and directories
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.abspath(__file__)) + "/data"

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Variables for tracking entire project
counter                 = 0
prj_num_of_lines        = 0
prj_num_of_vars         = 0
prj_num_of_func         = 0
prj_total_line_length   = 0
prj_var_camel_case      = 0
prj_var_snake_case      = 0
prj_func_camel_case     = 0
prj_func_snake_case     = 0
prj_lines_tabs_indent   = 0
prj_lines_space_indent  = 0
prj_lines_mixed_indent  = 0
prj_alone_brace         = 0
prj_space_brace         = 0
prj_no_space_brace      = 0
prj_tabbed_brace        = 0
prj_unknown_brace       = 0

commit_lines_added = 0
commit_lines_deleted = 0

gr = GitRepository(git_repo)

# Print Header for data
print("Commit,LOC,Avg Line Length,Lines Indented Tabs,Lines Indeneted Spaces,Lines Mixed Indent,Num Variables,Snake Vars,Camel Vars,Num Funcs,Snake Funcs,Camel Funcs,Alone Brace,Space Brace,No Space Brace,Tabbed Brace,Unknown Brace")

# Outer loop that steps through commits
for commit in RepositoryMining(git_repo).traverse_commits():
    counter = counter + 1
    #print('~~~~~~~~~~~~~~~~~~~~~~~~~~')
    #print("Commit " + str(counter))
    #print("Hash " + commit.hash + '\n')

    added_source_code       = ''
    deleted_source_code     = ''
    added_variable_names    = []
    deleted_variable_names  = []
    num_snake_case          = 0
    num_camel_case          = 0
    num_tabs_indent         = 0
    num_spaces_indent       = 0
    num_mixed_indent        = 0

    # Inner loops that steps trough each modification in the current commit
    for m in commit.modifications:
        file_extention = IsSourceFile(m.filename)
        if file_extention is not None:

            added_file_name = data_dir + "/" + str(counter) + "_added." + file_extention
            deleted_file_name = data_dir + "/" + str(counter) + "_deleted." + file_extention
            #print(m.filename)

            temp = open(added_file_name, 'w')
            temp.close()

            temp = open(deleted_file_name, 'w')
            temp.close()

            added_file = open(added_file_name, "r+")
            deleted_file = open(deleted_file_name,"r+")

            # Calculate line length
            parsed_lines = gr.parse_diff(m.diff)
            added = parsed_lines['added']
            deleted = parsed_lines['deleted']

            for x in added:
                if(x[1] != ''):
                    # Determine indentation
                    num_leading_spaces = CountLeadingSpaces(x[1])
                    num_leading_tabs   = CountLeadingTabs(x[1])

                    if(num_leading_spaces > 0 and num_leading_tabs == 0):
                        prj_lines_space_indent += 1 
                    elif(num_leading_spaces == 0 and num_leading_tabs > 0):
                        prj_lines_tabs_indent += 1 
                    elif(num_leading_spaces > 0 and num_leading_tabs > 0):
                        prj_lines_mixed_indent += 1
                        
                    prj_num_of_lines += 1
                    prj_total_line_length += len(x[1])
                    added_file.write(x[1])
                    added_file.write('\n')

                    index_of_brace = x[1].find('{')
                    
                    if(index_of_brace != -1):
                        if(x[1].strip() == '{'): # Standalone brace
                            prj_alone_brace += 1
                        elif(x[1][index_of_brace - 1] == " " and x[1][index_of_brace - 2] != '('):
                            prj_space_brace += 1
                        elif(x[1][index_of_brace - 1] != " " and x[1][index_of_brace - 1] != "\t"):
                            prj_no_space_brace += 1
                        elif(x[1][index_of_brace - 1] == "\t"):
                            prj_tabbed_brace += 1
                        else:
                            prj_unknown_brace += 1
                        
            for x in deleted:
                if(x[1] != ''):
                    # Determine indentation
                    num_leading_spaces = CountLeadingSpaces(x[1])
                    num_leading_tabs   = CountLeadingTabs(x[1])

                    if(num_leading_spaces > 0 and num_leading_tabs == 0):
                        prj_lines_space_indent -= 1
                        if prj_lines_space_indent < 0:
                            prj_lines_space_indent = 0
                    elif(num_leading_spaces == 0 and num_leading_tabs > 0):
                        prj_lines_tabs_indent -= 1 
                        if prj_lines_tabs_indent < 0:
                            prj_lines_tabs_indent = 0
                    elif(num_leading_spaces > 0 and num_leading_tabs > 0):
                        prj_lines_mixed_indent -= 1
                        if prj_lines_mixed_indent < 0:
                            prj_lines_mixed_indent = 0

                    prj_num_of_lines -= 1
                    if prj_num_of_lines < 0:
                        prj_num_of_lines = 0
                    prj_total_line_length -= len(x[1])
                    if prj_total_line_length < 0:
                        prj_total_line_length = 0
                    deleted_file.write(x[1])
                    deleted_file.write('\n')

                    index_of_brace = x[1].find('{')
                    
                    if(index_of_brace != -1):
                        if(x[1].strip() == '{'): # Standalone brace
                            prj_alone_brace -= 1
                            if prj_alone_brace < 0:
                                prj_alone_brace = 0
                        elif(x[1][index_of_brace - 1] == " " and x[1][index_of_brace - 2] != '('):
                            prj_space_brace -= 1
                            if prj_space_brace < 0:
                                prj_space_brace = 0
                        elif(x[1][index_of_brace - 1] != " " and x[1][index_of_brace - 1] != "\t"):
                            prj_no_space_brace -= 1
                            if prj_no_space_brace < 0:
                                prj_no_space_brace = 0
                        elif(x[1][index_of_brace - 1] == "\t"):
                            prj_tabbed_brace -= 1
                            if prj_tabbed_brace < 0:
                                prj_tabbed_brace = 0
                        else:
                            prj_unknown_brace -= 1
                            if prj_unknown_brace < 0:
                                prj_unknown_brace = 0

            added_file.close()
            deleted_file.close()
                    
            #srcml stuff
            added_xml = GetSRCML(added_file_name)
            deleted_xml = GetSRCML(deleted_file_name)

            added_variable_names = GetVariableNamesFromSRCML(added_xml)
            deleted_variable_names = GetVariableNamesFromSRCML(deleted_xml)

            added_func_names = GetFunctionNamesFromSRCML(added_xml)
            deleted_func_names = GetFunctionNamesFromSRCML(deleted_xml)

            for added in added_func_names:
                prj_num_of_func += 1

                if IsCamelCase(added):
                    prj_func_camel_case += 1
                elif IsSnakeCase(added):
                    prj_func_snake_case += 1

            for deleted in deleted_func_names:
                prj_num_of_func -= 1
                if prj_num_of_func < 0:
                    prj_num_of_func = 0

                if IsCamelCase(deleted):
                    prj_func_camel_case -= 1
                    if prj_func_camel_case < 0:
                        prj_func_camel_case = 0
                elif IsSnakeCase(deleted):
                    prj_func_snake_case -= 1
                    if prj_func_snake_case < 0:
                        prj_func_snake_case = 0

            for added in added_variable_names:
                prj_num_of_vars += 1

                if IsCamelCase(added):
                    prj_var_camel_case += 1
                elif IsSnakeCase(added):
                    prj_var_snake_case += 1

            for deleted in deleted_variable_names:
                prj_num_of_vars -= 1
                if prj_num_of_vars < 0:
                    prj_num_of_vars = 0

                if IsCamelCase(deleted):
                    prj_var_camel_case -= 1
                    if prj_var_camel_case < 0:
                        prj_var_camel_case = 0
                elif IsSnakeCase(deleted):
                    prj_var_snake_case -= 1
                    if prj_var_snake_case < 0:
                        prj_var_snake_case = 0

    #String to print
    output = str(counter) + ","
    output += str(prj_num_of_lines) + ","
    if(prj_num_of_lines > 0):
        output += str(prj_total_line_length / prj_num_of_lines) + ","
    else:
        output += "0,"
    output += (str(prj_lines_tabs_indent)) + ","
    output += (str(prj_lines_space_indent)) + ","
    output += (str(prj_lines_mixed_indent)) + ","
    output += (str(prj_num_of_vars)) + ","
    output += (str(prj_var_snake_case)) + ","
    output += (str(prj_var_camel_case)) + ","
    output += (str(prj_num_of_func)) + ","
    output += (str(prj_func_snake_case)) + ","
    output += (str(prj_func_camel_case)) + ","
    output += (str(prj_alone_brace))  + ","
    output += (str(prj_space_brace))  + ","
    output += (str(prj_no_space_brace))  + ","
    output += (str(prj_tabbed_brace))  + ","
    output += (str(prj_unknown_brace)) 

    print(output)
