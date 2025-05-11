from cache_tables import generate_cache

def generate(data):

  # generate_cache(data, num_ways, index_bits, num_addr)
  
  generate_cache(data, 'cache', 2, 2, 1)

  data['params']['cache2'] = data['params']['cache']
  data['correct_answers']['cache2'] = data['correct_answers']['cache']

  return data
