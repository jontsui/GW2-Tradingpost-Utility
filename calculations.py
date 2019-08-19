import database
import threadpool
import gw2api


def crafting_cost(item_identifier, *, debug = False):
    ''' Creates 1 (+ 1) connections and N threads per call (N = # ingredients in base list).
    Arguments: 'item_identifier' is either an item name or id
               
               'info' is a flag which when set forces function to return a list 
               of dictionaries with full information about ingredient costs
               Return value: [{item_id: , item_name, count:, unit_cost: ,total_cost: }, ...]
    '''

    with database.Gw2Database() as conn: # Connection here
        base_ingredients = conn.base_ingredients(item_identifier)
    
    def worker(ingredient_dict):
        '''Argument is a dictionary from base ingredients list.  
        Looks up the item_id against gw2 api's TP listings.
        Returns ingredient dictionary with two additional keys - 'unit_cost' and 'total_cost' '''
        
        item_id = ingredient_dict['item_id']
        
        # We assume that the priority of where you buy the item from will be 
        # 1) vendor, 2) buy listings, 3) sell listings
        with database.Gw2Database() as conn: # Connection here
            unit_cost = conn.vendor_price(item_id)
        if unit_cost is None:
            unit_cost = gw2api.v2_listings_buy(item_id)
            if unit_cost == 0:
                unit_cost = gw2api.v2_listings_sell(item_id)
                # Defaults to 0 all listings are NA

        ingredient_dict['unit_cost'] = unit_cost
        ingredient_dict['total_cost'] = unit_cost * ingredient_dict['count']

        return ingredient_dict

    pool = threadpool.ThreadPool(len(base_ingredients))
    for ingredient_dict in base_ingredients:
        pool.add_task(worker, ingredient_dict)
    pool.start()
    pool.join()
    pool.stop_threads()

    final_cost = sum([item_dict['total_cost'] for item_dict in pool.results])
    
    
    if debug:
        # Print all elements in results
        for ingredient_dict in pool.results:
            print(ingredient_dict)
        print(final_cost)
        import webbrowser
        webbrowser.open('https://wiki.guildwars2.com/wiki/'+ item_identifier)

    # Otherwise just return sum of costs
    return final_cost

def watchlist_compute(input_file, output_file, *, debug = False):
    if debug:
        import time
        start = time.time()
    
    '''Reads item names from input_file and writes crafting cost, tp sell price, 
    and ROI info for each item to output_file.
    Arguments: input_file, output_file'''

    # Lookup each item name in file, convert to ID, then add to items_to_compute
    with database.Gw2Database() as conn:
        with open(input_file) as fin:
            items_to_compute = []
            for line in fin:
                item_name = line.rstrip('\n')
                item_id = conn.name_to_id(item_name)
                items_to_compute.append({'item_id': item_id , 'item_name': item_name})
    
    # Create a blank file, write current time, and column headers
    import datetime
    with open(output_file, 'w') as newfile:
        newfile.write(str(datetime.datetime.now()) + '\n')
        column_labels = 'name', 'craft_cost', 'sell_listing', 'ROI'
        newfile.write('{:>35} {:>20} {:>15} {:>15}\n'.format(*column_labels))


    def worker(item_dict):
        # item_dict - {'item_id': <>, 'item_id': <>}'''
        if debug:
            print('Starting new task')
        
        _id = item_dict['item_id']
        
        item_dict['craft_cost'] = crafting_cost(_id)
        item_dict['sell_listing'] = gw2api.v2_listings_sell(_id)

        # item_dict - {'item_id': <>, 'item_id': <>, 'crafting_cost': <>, 'sell_listing': <>}
        return item_dict

    pool = threadpool.ThreadPool(15)
    for item_dict in items_to_compute:
        pool.add_task(worker, item_dict)
    pool.start()
    pool.join()
    pool.stop_threads

    if debug:
        for res in pool.results:
            print(res)
        print(len(pool.results), len(items_to_compute)) # Check for correctness
        end = time.time()
        print(end-start) # Get runtime
        return
    
    with open(output_file, 'a+') as fout:
        for item_dict in pool.results:
            line = (item_dict['item_name'], 
                  _gold(item_dict['craft_cost']),
                  _gold(item_dict['sell_listing']), 
                  _roi(item_dict['craft_cost'], 
                  item_dict['sell_listing']))
            fout.write('{:>35} {:>20} {:>15} {:>15}\n'.format(*line))
        
def _roi(craft, sell):
    '''Return on investment, returns an integer'''
    try:
        # Potentially DivisionByZero Exception
        roi = int((sell*0.85-craft)/craft*100)
    except:
        roi = 0
    return str(roi)

def _gold(value): #123793
    '''Returns a string representing an integer's equivalent gold value'''
    gold = value//10000
    silver = (value-gold*10000)//100
    copper = (value-gold*10000-silver*100)
    return '{}g {}s {}c'.format(gold, silver, copper)

def __remove_quotes(input_file):
    L = []
    with open(input_file, 'r+') as f: 
        for line in f:
            line = line.rstrip('\n')
            line = line.strip('"')
            L.append(line)
        f.seek(0)
        f.truncate()
        for string in L:
            f.write(string + '\n')
    
if __name__ == '__main__':

    def unit_test1():
        #Oiled Forged Scrap: 82796
        #Green Torch Handle recipe: 4458
        #Rough Sharpening Stone: 9431
        #Lump of Primordium: 19924
        #Gossamer Patch: 76614
        x = crafting_cost("Oiled Forged Scrap", debug = False)
        print(x)
    
    def unit_test2():
        import paths
        watchlist_compute(paths.watchlists + 'runes.csv', 
                          paths.watchlists + 'runes_output.txt', debug = False)
    
