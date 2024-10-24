from supabase import create_client, Client

# Supabase project details
url = 'https://vqlylnfgxeimreedequm.supabase.co'  # Replace with your Supabase URL
try:
    with open('supabase_admin_key.txt','r') as f:
        key = f.read()
        f.close()
except FileNotFoundError:
    raise FileNotFoundError('Supabase Admin Key file not found, If you aren\'t Solomon or Vincent, you shouldn\'t be running this tool.')
supabase: Client = create_client(url, key)

valid_data = {}
response = supabase.rpc('get_lb', {}).execute().data
for row in response:
    valid_data[row['username']] = [row['score'],row['lines']]

while True:
    response = supabase.rpc('get_lb', {}).execute().data
    if response != None:
        new_data = {}
        for row in response:
            new_data[row['username']] = [row['score'],row['lines']]
        new_valid_data = new_data.copy()
        for name,[score,lines] in new_data.items():
            if not name in valid_data:
                valid_data[name] = [0,0]
            [v_score,v_lines] = valid_data[name]
            valid = True
            if (lines-v_lines) not in [0,1,2,3,4]:
                new_valid_data[name][1] = v_lines
                print(f'{name.upper()}\'s lines jumped too high! From {v_lines} to {lines} (Difference of {lines-v_lines}, Allowed Difference: 4).')
                valid = False
            if (score-v_score) > (1200*(new_valid_data[name][1]+1))+40:
                new_valid_data[name][0] = v_score
                print(f'{name.upper()}\'s score jumped too high! From {v_score} to {score} (Difference of {score-v_score}, Allowed Difference: {(1200*((new_valid_data[name][1]//10)+1))+40}).')
                valid = False
            if not valid:
                print(f'    Resetting {name}\'s scores and lines to appropriate values.')
                response = (supabase.table('leaderboard')
                    .update({'score':new_valid_data[name][0],'lines':new_valid_data[name][1]})
                    .eq('username', name)
                    .execute()
                )
                print('    Update successful.')
            valid_data[name] = new_valid_data[name]