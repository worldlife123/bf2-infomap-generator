# ----------------------------------------------
# FIRE'S SIMPLE CON PARSER
#
# CONTACT:
# fire_1@gmx.de
# www.flmod.com
#
# USAGE (READ):
# config = readCon(file)
# Returns a list: [{key1: [values1]}, {key2: [values2, values2]}, ...]
#
# USAGE (WRITE):
# success = writeCon(config, file)
# ----------------------------------------------

# ----------------------------------------------
# Imports
# ----------------------------------------------
#from bf2 import g_debug
g_debug = 0

def readCon(conFile):
    config = []
    rem = False
    
    # ----------------------------------------------
    # Open the file
    # ----------------------------------------------
    if g_debug:
        print 'Reading CON file...'
    
    try:
        f = file(conFile, 'r')
        lines = f.readlines()
        f.close()
    except IOError: # Damn..
        if g_debug:
            print 'Error while reading CON file!!'
        
        return config

    
    for line in lines:
        # ----------------------------------------------
        # Replace tabs etc.
        # ----------------------------------------------
        line = line.replace('\t', ' ')
        line = line.strip(' \n')

        # ----------------------------------------------
        # Remove comments
        # ----------------------------------------------
        if line[:4].lower().strip() == 'rem':
            continue
        elif line[:9].lower().strip() == 'beginrem':
            rem = True
            continue
        elif line[:7].lower().strip() == 'endrem':
            rem = False
            continue
        else:
            if rem:
                continue

        # ----------------------------------------------
        # Find the end of the key
        # ---------------------------------------------- 
        pos = line.find(' ')
        if pos < 0: # Not found :(
			key = line
			values = []
			#modified by worldlife in order to get "endIf" command
        # ----------------------------------------------
        # Get the key
        # ---------------------------------------------- 
        else: 
			key = line[:pos]

			# ----------------------------------------------
			# Get the values
			# ---------------------------------------------- 
			values = line[pos + 1:].split(' ')
			for value in values:
				value = value.strip(' ')

        config.append({key: values})


    # ----------------------------------------------
    # Return the list
    # ---------------------------------------------- 
    return config


# -------------------------------------------------------------------------------------------- 


def writeCon(config, conFile):
    # ----------------------------------------------
    # Open the file
    # ----------------------------------------------
    if g_debug:
        print 'Writing CON file...'
    
    try:
        f = file(conFile, 'w+')
        pass
    except IOError: # Damn..
        return False
    
    data = 'rem *** Created with FiRe\'s CON parser ***\n\n'


    # ----------------------------------------------
    # Create the Con file
    # ----------------------------------------------
    for conf in config:
        # ----------------------------------------------
        # Add the key
        # ----------------------------------------------
        data += conf.items()[0][0]
        
        # ----------------------------------------------
        # Add the values
        # ----------------------------------------------
        for key in conf.items()[0][1]:
            data += ' ' + key
        data += '\n'


    # ----------------------------------------------
    # Write the config to file
    # ----------------------------------------------
    try:
        f.write(data)
        f.close()
    except IOError:
        if g_debug:
            print 'Error while writing CON file!!'
        return False
    else:
        return True
