# !!!!!!!!!!!!!!!!!!!
#  WARNING: VERY BAD
# !!!!!!!!!!!!!!!!!!!
import re

def unparse(readdict, repr_keys=True, repr_values=True):
	"""Convert dictionary to WeaponScript format as a string."""
	global strtoreturn, indent
	keyvalueseparator = "\t\t"
	strtoreturn = ""
	indent = ""

	def _newsubkey(item, keyname):
		global strtoreturn, indent
		strtoreturn = (strtoreturn + indent + str(keyname) + '\n'
					   + indent + '{' + '\n')
		indent = indent + "\t"
		for k, v in item.items():
			if type(v) is dict:
				_newsubkey(item[k], k)
			else:
				strtoreturn = (strtoreturn + indent + str(k) + keyvalueseparator + str(v) + "\n")
		indent = indent[1:]
		strtoreturn = strtoreturn + indent + "}" + "\n"

	for key, value in readdict.items():
		if type(value) is dict:
			_newsubkey(readdict[key], key)
		else:
			strtoreturn = (strtoreturn + indent + str(key)
						 + keyvalueseparator + str(value) + "\n")
	return strtoreturn

def parse(file, printoutput=False, eval_keys=False, eval_values=False):
	"""
	Parse Source Engine WeaponScript files.

	Arguments:
		printoutput (bool) - If the script should print details.
		eval_keys (bool) - If the script should attempt to evaluate keys
		eval_values (bool) - If the script should attempt to evaluate values

	The script does not evaluate keys and values that are defined variables.

	Returns 3 things in a tuple:
		1. Parsed data as a dictionary
		2. Set of lines with unevaluated keys
		3. Set of lines with unevaluated values

	Format rules I made up for WeaponScript:
		1. declaring a key and value pair should be in their own line
		2. declaring a key and a subkey should be in their own separate lines
		3. two keys should should not wait for a '{'
		4. declaring the end of a subkey ('}') should only be done ONCE in one line
		5. treat everything else as either a key waiting for a bracket or a key-value pair
	"""
	global dicttoreturn, current_subkey
	dicttoreturn = {}
	current_subkey = None
	current_line = 0
	subkey_heirarchy = []
	subkey_iswaiting = False
	unevaluated_keys_lines = set()
	unevaluated_values_lines = set()

	def _opensubkey(_newsubkey):
		global dicttoreturn, current_subkey, previous_subkey
		if current_subkey is not None:
			previous_subkey = current_subkey
			current_subkey[_newsubkey] = {}
			current_subkey = current_subkey[_newsubkey]
			if not subkey_iswaiting:
				subkey_heirarchy.append(_newsubkey)
		else:
			previous_subkey = None
			dicttoreturn[_newsubkey] = {}
			current_subkey = dicttoreturn[_newsubkey]
			if not subkey_iswaiting:
				subkey_heirarchy.append(_newsubkey)

	def _closesubkey(current_line):
		global current_subkey, previous_subkey
		if current_subkey is None:
			raise SyntaxError(ERROR_TXT_UNMATCHED_CLOSE)
		subkey_heirarchy.pop()
		current_subkey = previous_subkey

	for line in file:
		current_line += 1

		OUTPUT_TXT_KEY_AND_VALUE = "\tDetected key and value pair"
		OUTPUT_TXT_CLOSINGBRACKETS = "\tDetected '}'"
		OUTPUT_TXT_BRACKET_FOR_SUBKEY = "\tDetected bracket for waiting Subkey"
		OUTPUT_TXT_SUBKEY = "\tDetected key that is waiting for a bracket"
		ERROR_TXT_INFO = f', line {current_line}, in file {file.name}'
		ERROR_TXT_UNMATCHED_CLOSE = "Unmatched '}'" + ERROR_TXT_INFO
		ERROR_TXT_NO_KEY_FOR_SUBKEY = "Open curly bracket for subkey isn't assigned a key" + ERROR_TXT_INFO
		ERROR_TXT_MULTIPLE_WAITING_KEYS = "Multiple keys are waiting for a bracket" + ERROR_TXT_INFO

		split = re.split(r"(?=[\t\n ])\t+|(?=[\t\n ]) ", line.split("//", 1)[0], maxsplit=2)   # Split line
		for i in range(len(split)):
			split[i] = split[i].replace("\t","")
			split[i] = split[i].replace("\n","")
		split = [i for i in split if i != '']

		if printoutput: 
			print(f"Line {current_line}:" ,"\n"
				   "\tlen:", str(len(split)) ,"\n"
				   "\tsplit:", split         ,"\n")

		if split is None: continue

		if len(split) > 1:
			split1, split2 = split[0], split[1]

			try:
				if eval_keys: outkey = eval(split1)
				else: outkey = split1
				if split1 in list(locals().keys()) + list(globals().keys()):
					outkey = split1
					unevaluated_keys_lines.add(current_line)
			except:
				outkey = split1
				unevaluated_keys_lines.add(current_line)

			try:
				if eval_values: outvalue = eval(split2)
				else: outvalue = split2
				if split2 in list(locals().keys()) + list(globals().keys()):
					outvalue = split2
					unevaluated_values_lines.add(current_line)
			except:
				outvalue = split2
				unevaluated_values_lines.add(current_line)

			if printoutput: print(OUTPUT_TXT_KEY_AND_VALUE)
			current_subkey[outkey] = outvalue

		elif len(split) == 1:
			split1 = split[0]
			match split1:
				case r'{':
					if len(subkey_heirarchy) == 0: raise SyntaxError(ERROR_TXT_NO_KEY_FOR_SUBKEY)
					_opensubkey(subkey_heirarchy[-1])
					subkey_iswaiting = False
					if printoutput: print(OUTPUT_TXT_BRACKET_FOR_SUBKEY)

				case r'}':
					_closesubkey(current_line)
					if printoutput: print(OUTPUT_TXT_CLOSINGBRACKETS)

				case default:
					if subkey_iswaiting == True: raise SyntaxError(ERROR_TXT_MULTIPLE_WAITING_KEYS)
					subkey_iswaiting = True
					try:
						if eval_keys: outkey = eval(split1)
						else: outkey = split1
						if split1 in list(locals().keys()) + list(globals().keys()):
							outkey = split1
							unevaluated_keys_lines.add(current_line)
					except:
						unevaluated_keys_lines.add(current_line)
						outkey = split1

					subkey_heirarchy.append(outkey)
					if printoutput: print(OUTPUT_TXT_SUBKEY)

		line_has_comment = len(line.split("//", 1)) == 2
		if printoutput:
			if line_has_comment: print("\tDetected comment line")
			print()
	return (dicttoreturn, unevaluated_keys_lines, unevaluated_values_lines)
