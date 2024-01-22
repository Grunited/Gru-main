lines = docstring.strip().split('\n')
summary = lines[0].strip()

# Extract parameters
param_pattern = r':param\s+(\w+):\s*((?:(?!:param).)*)'
params = re.findall(param_pattern, docstring)
params_list = []
for param in params:
    name = param[0]
    description = param[1].strip()
    params_list.append({
        'name': name,
        'type': None,
        'description': description
    })

# Extract returns
return_pattern = r':return[s]?:\s*((?:(?!:param).)*)'
returns = re.findall(return_pattern, docstring)
if returns:
    returns = returns[0].strip()
else:
    returns = None

json_dict = {
    'summary': summary,
    'params': params_list,
    'returns': returns
}

print(json_dict)