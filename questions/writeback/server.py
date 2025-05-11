from cache_tables import generate_cache
import random

def generate(data):

  # generate_cache(data, num_ways, index_bits, num_addr)
  addr_hex_size = random.randint(2,4)
  addr_bit_size = addr_hex_size * 4  

  # set to 4 or 8 sets 
  index_bits = random.randint(2,3)   # 4- or 8- sets

  # hardcode to 4 Bytes per block
  offset_bits = random.randint(1,3)


  generate_cache(data, 'cache', addr_bits=addr_bit_size, set_bits=index_bits, block_bits=offset_bits, ways=1, 
    show_valid=True, show_dirty=True, partial_empty=True)

  if data['correct_answers']['cache_access'][0]['hit'] == True:
    data['correct_answers']['ans'] = data['correct_answers']['cache_access'][0]['data']
  elif data['correct_answers']['cache_access'][0]['writeback'] == False:
    data['correct_answers']['ans'] = 'replace'
  else:
    data['correct_answers']['ans'] = 'writeback'

  return data
