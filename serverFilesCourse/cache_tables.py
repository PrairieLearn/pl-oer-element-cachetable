import random
import string
import math
from random import choice


DATA_MEM = []
CACHE = []
VALID = []

def generate_cache(data, answers_name, ways=2, set_bits=1, num_addr=1, block_bits=1, 
                  addr_bits=5, show_valid=False, empty_cache=False, partial_empty=False, 
                  base='hex', min_hits=0, min_miss=0, address_list=[], show_dirty = False):
  '''
  Utility for generating caches and sequences of access for the pl-cache-table and pl-cache-access-table elements. 
  The script exports all parameters that can be passed directly to pl-cache-table and/or pl-cache-access-table
  data['params']['mem_table'] can be passed to pl-array-input to display a data memory
  data['params'][answers_name] and data['correct_answers'][answers_name] will be read by pl-cache-table automatically if its answers-name parameter matches answers_name
  data['correct_answers'][f'{answers_name}_access'] = access_table will be read by pl-cache-access-table automatically if its answers-name parameter matches answers_name

  ways sets the set-associativity of the cache
  set_bits determines the number of bits in the set index
  num_addr determines the number of memory address that are accessed
  block_bits determines the number of bits in the block offset
  addr_bits determines the number of bits in the data memory addresses
  show_valid determines whether valid bits are shown in the cache
  empty_cache determines whether the cache starts with all blocks being invalid
  base determines the base used to represent the tag and memory addresses

  Default values are chosen so that the cache and data memory are fairly small so that they can be easily seen on the screen. 
  We do not recommend increasing the default values by much more than 1
  '''

  # params for pl-cache-table attributes
  data['params']['answers_name'] = answers_name
  data['params']['num_ways'] = ways
  data['params']['set_bits'] = set_bits
  data['params']['block_bits'] = block_bits
  data['params']['addr_bits'] = addr_bits
  data['params']['show_valid'] = show_valid
  data['params']['show_dirty'] = show_dirty
  data['params']['empty_cache'] = empty_cache
  data['params']['display_base'] = base.lower()

  #CACHE parameters
  mem_size = 2**addr_bits
  cache_sets = 2**set_bits
  block_size = 2**block_bits
  data['params']['memory_size'] = mem_size
  data['params']['cache_sets'] = cache_sets
  data['params']['cache_size'] = ways * cache_sets * block_size
  data['params']['block_size'] = block_size


  tag_bits = addr_bits - set_bits - block_bits
  tag_hex_size = math.ceil(tag_bits / 4)

  max_tag = 2**tag_bits - 1

  # make sure that cache configuration is possible
  if tag_bits <= 0:
    raise ValueError(
        f'The size of the cache is too big relative to the size of the memory. Make sure addr_bits > set_bits + block_bits + 1, preferably even bigger'
    )
    return

  base = base.lower()
  if base != 'hex' and base != 'bin':
    raise ValueError(
        f'base must be "hex" or "bin"'
    )
    return

  if ways * cache_sets * block_size > mem_size:
    raise ValueError(
        f'Total cache size cannot be larger than the data memory'
    )
    return

###########################
### CREATE MEMORY TABLE ###
###########################

  create_mem_table(data, mem_size)

###################################
### Generate initial CACHE data ###
###################################

  way_list = list(range(ways))
  cache_block = {}

  for x in range(cache_sets):
    # generate 1 tag per way
    tags = []
    valid = []
    dirty = []
    blocks = [[0 for j in range(block_size)] for i in range(ways)]

    for way in range(ways):
      if empty_cache and show_valid:
        valid.append(0)
        dirty.append(0)
        tags.append(random.randint(0, max_tag))
        for offset in range(block_size):
          blocks[way][offset] = str(random.randint(0,255))
      elif empty_cache:
        valid.append(0)
        dirty.append(0)
        tags.append('')
        for offset in range(block_size):
          blocks[way][offset] = ''  
      elif partial_empty and show_valid:
        temp = random.randint(0,1)
        valid.append(temp)
        if temp == 0:
          dirty.append(0)
        else:
          tempd = random.randint(0,3)
          if tempd == 0:
            dirty.append(0)
          else:
            dirty.append(1)
        tags.append(random.randint(0, max_tag))
        if temp == 0:
          for offset in range(block_size):
            blocks[way][offset] = str(random.randint(0,255))
        else:
          if way > 0:
            while tags[way] in tags[:way]:
              tags[way] = random.randint(0, max_tag)
          addr = (tags[way] * cache_sets + x) * block_size
          for offset in range(block_size):
            blocks[way][offset] = str(DATA_MEM[addr + offset])
      else:
        valid.append(1)
        dirty.append(random.randint(0,1))
        tags.append(random.randint(0, max_tag))
        if way > 0:
          while tags[way] in tags[:way]:
            tags[way] = random.randint(0, max_tag)
        addr = (tags[way] * cache_sets + x) * block_size
        for offset in range(block_size):
          blocks[way][offset] = str(DATA_MEM[addr + offset])

    # generate LRU FSM
    lru_list = random.sample(way_list,len(way_list))
    cache_block = {'tags': tags, 'lru': lru_list, 'blocks': blocks, 'valid': valid, 'dirty': dirty}
    VALID.append(valid)
    CACHE.append(cache_block)
  
  ### Initial state of the cache. Will be used by pl-cache-table
  data['params'][answers_name] = stringify_cache(tag_bits, tag_hex_size, base)

###########################################
### Create addresses and simulate cache ###
###########################################
  if min_miss + min_hits > num_addr and address_list == []:
    raise ValueError("The min_miss + min_hits cannot exceed num_addr")

  if address_list != []:
    access_cache(data, answers_name, address_list, block_bits, set_bits, ways, addr_bits, base)

    ### Final state of the cache. Will be used by pl-cache-table
    data['correct_answers'][answers_name] = stringify_cache(tag_bits, tag_hex_size, base)

    return

  hit_miss_list = make_hit_list(num_addr, min_hits, min_miss, empty_cache)
  
  feedback_table = []
  access_table = []
  for x in range(num_addr):
    # Generate random address and update cache
    acc_idx, acc_tag, way = determine_block(cache_sets, ways, max_tag, hit_miss_list[x])

    acc_off = random.randint(0, block_size-1)

    addr = (acc_tag * cache_sets + acc_idx) * block_size + acc_off

    if base == 'hex':
      str_address = f'{addr:#0{math.ceil(addr_bits / 4) + 2}x}'
      if cache_sets > 1:
        feedback = {
          'access': x,
          'tag': f'<code>{str_address}</code> / {block_size} / {cache_sets} = {hex(acc_tag)}',
          'index': f'<code>{str_address}</code> / {block_size} % {cache_sets} = {hex(acc_idx)}',
          'offset': f'<code>{str_address}</code> % {block_size} = {hex(acc_off)}',
        }
      else:
        feedback = {
          'access': x,
          'tag': f'<code>{str_address}</code> / {block_size} = {hex(acc_tag)}',
          'offset': f'<code>{str_address}</code> % {block_size} = {hex(acc_off)}',
        }
    else:
      str_address = f'{addr:0{addr_bits}b}'
      str_address = ' '.join(str_address[::-1][i:i+4] for i in range(0, len(str_address), 4))[::-1]
      str_address = '0b' + str_address
      if cache_sets > 1:
        feedback = {
          'access': x,
          'tag': f'Tag = {acc_tag:0{tag_bits}b}',
          'index': f'Index = {acc_idx:0{set_bits}b}',
          'offset': f'Offset = {acc_off:0{block_bits}b}',
        }
      else:
        feedback = {
          'access': x,
          'tag': f'Tag = {acc_tag:0{tag_bits}b}',
          'offset': f'Offset = {acc_off:0{block_bits}b}',
        }

    writeback = update_cache(acc_tag, acc_idx, addr)
    access = {
      'address': str_address,
      'hit': hit_miss_list[x],
      'data': None,
      'writeback': writeback,
    }
    if hit_miss_list[x]:
      access['data'] = CACHE[acc_idx]['blocks'][way][acc_off]
    access_table.append(access)
    feedback_table.append(feedback)

  ### List of memory accesses and their hits/misses in cache. Will be used by pl-cache-access-table
  data['correct_answers'][f'{answers_name}_access'] = access_table
  data['params']['tio_sequence'] = feedback_table
  ### Final state of the cache. Will be used by pl-cache-table
  data['correct_answers'][answers_name] = stringify_cache(tag_bits, tag_hex_size, base)

  return

def update_cache(acc_tag, acc_idx, addr):
  ### Updates the contents of the cache given an address, tag, and index
  lru_list = CACHE[acc_idx]['lru']
  ways = len(lru_list)

  block_size = len(CACHE[acc_idx]['blocks'][lru_list[0]])
  addr = addr // block_size * block_size # strip offset

  writeback = False
  for way in range(ways):
    if (CACHE[acc_idx]['tags'][way] == acc_tag) and (CACHE[acc_idx]['valid'][way] == 1):
      CACHE[acc_idx]['lru'] = update_lru(way, lru_list)
      return writeback
  replaced_way = lru_list[0]
  if CACHE[acc_idx]['valid'][replaced_way] == 1 and CACHE[acc_idx]['dirty'][replaced_way] == 1:
    writeback = True
  CACHE[acc_idx]['tags'][replaced_way] = acc_tag
  CACHE[acc_idx]['valid'][replaced_way] = 1
  CACHE[acc_idx]['dirty'][replaced_way] = 0
  for off in range(block_size):
    CACHE[acc_idx]['blocks'][replaced_way][off] = str(DATA_MEM[addr+off])
  CACHE[acc_idx]['lru'] = update_lru(lru_list[0], lru_list)

  return writeback
def update_lru(way, lru_list):
  ### Updates lru fsm for one set given the way that was accessed
  ways = len(lru_list)

  for x in range(ways-1):
    if way == lru_list[x]:
      for y in range(x,len(lru_list)-1):
        lru_list[y] = lru_list[y+1]
      lru_list[len(lru_list)-1] = way
      return lru_list
  return lru_list

def stringify_cache(tag_bits, tag_hex_size, base):
  ### converts CACHE to a dictionary of strings to be used by pl-cache-table
  str_cache = []
  for x in range(len(CACHE)):
    tags = []
    lru = []
    blocks = []
    valid = []
    dirty = []
    for y in range(len(CACHE[x]['tags'])):
      if CACHE[x]['tags'][y] != '':
        if base == 'hex':
          tags.append(f'{CACHE[x]["tags"][y]:#0{tag_hex_size + 2}x}')
        else:
          tags.append(f'{CACHE[x]["tags"][y]:0{tag_bits}b}')
      else:
        tags.append('')
      lru.append(str(CACHE[x]['lru'][y]))
      valid.append(str(CACHE[x]['valid'][y]))
      dirty.append(str(CACHE[x]['dirty'][y]))
      block = []
      for z in range(len(CACHE[x]['blocks'][y])):
        block.append(CACHE[x]['blocks'][y][z])
      blocks.append(block)

    str_cache.append({'tags': tags, 'lru': lru, 'blocks': blocks, 'valid': valid, 'dirty':dirty})
  
  return str_cache

def create_mem_table(data, mem_size):
  mem_table = []

  for x in range(mem_size):
    value = random.randint(0,255)
    DATA_MEM.append(value)
    mem_table.append(value)

  ### Parameters to be provided to pl-array-input element
  ### to represent data memory as an array
  data['params']['mem_table'] = mem_table
  
def make_hit_list(num_addr, min_hits, min_miss, empty_cache):
  hit_miss_list = [False] * min_miss + [True] * min_hits
  if not empty_cache:
    hit_miss_list += [random.choice([False, True]) for _ in range(num_addr - min_hits - min_miss)]
    random.shuffle(hit_miss_list)
  else:
    hit_miss_list += [random.choice([False, True]) for _ in range(num_addr - min_hits - min_miss - 1)]
    random.shuffle(hit_miss_list)
    hit_miss_list.insert(0, False)
  return hit_miss_list

def determine_block(cache_sets, ways, max_tag, hit):
  valid_list = []
  invalid_list = []
  for index in range(cache_sets):
    for way in range(ways):
      if VALID[index][way] == 1:
        valid_list.append([index,way])
      else:
        invalid_list.append([index,way])

  if hit:
    chosen_block = random.choice(valid_list)

    acc_idx = chosen_block[0]
    way = chosen_block[1]
    acc_tag = CACHE[acc_idx]["tags"][way]

  elif invalid_list == []:
    chosen_block = random.choice(valid_list)
    acc_idx = chosen_block[0]
    way = chosen_block[1]
    tags = list(range(0,max_tag+1))
    for way in range(ways):
      tags.remove(CACHE[acc_idx]["tags"][way])
    acc_tag = random.choice(tags)
  else:
    access_empty = random.choice([True, False])
    if valid_list == [] or access_empty:
      chosen_block = random.choice(invalid_list)
      acc_idx = chosen_block[0]
      way = chosen_block[1]
      acc_tag = CACHE[acc_idx]["tags"][way]
    else:
      chosen_block = random.choice(valid_list)
      acc_idx = chosen_block[0]
      way = chosen_block[1]
      tags = list(range(0,max_tag+1))
      for way in range(ways):
        if CACHE[acc_idx]["valid"][way] == 1:
          tags.remove(CACHE[acc_idx]["tags"][way])
      acc_tag = random.choice(tags)

  return acc_idx, acc_tag, way

def access_cache(data, answers_name, address_list, block_bits, set_bits, ways, addr_bits, base):
  
  access_table = []
  feedback_table = []
  index = []
  tag = []
  block_size = 2**block_bits
  cache_sets = 2**set_bits
  tag_bits = addr_bits - block_bits - set_bits
  for x in range(len(address_list)):
    # Generate random address and update cache
    addr = address_list[x]
    acc_off = addr % block_size
    acc_idx = addr // block_size % cache_sets
    acc_tag = addr // block_size // cache_sets

    if base == 'hex':
      str_address = f'{addr:#0{math.ceil(addr_bits / 4) + 2}x}'
      if cache_sets > 1:
        feedback = {
          'access': x,
          'tag': f'<code>{str_address}</code> / {block_size} / {cache_sets} = {hex(acc_tag)}',
          'index': f'<code>{str_address}</code> / {block_size} % {cache_sets} = {hex(acc_idx)}',
          'offset': f'<code>{str_address}</code> % {block_size} = {hex(acc_off)}',
        }
      else:
        feedback = {
          'access': x,
          'tag': f'<code>{str_address}</code> / {block_size} = {hex(acc_tag)}',
          'offset': f'<code>{str_address}</code> % {block_size} = {hex(acc_off)}',
        }
    else:
      str_address = f'{addr:0{addr_bits}b}'
      str_address = ' '.join(str_address[::-1][i:i+4] for i in range(0, len(str_address), 4))[::-1]
      str_address = '0b' + str_address
      if cache_sets > 1:
        feedback = {
          'access': x,
          'tag': f'Tag = {acc_tag:0{tag_bits}b}',
          'index': f'Index = {acc_idx:0{set_bits}b}',
          'offset': f'Offset = {acc_off:0{block_bits}b}',
        }
      else:
        feedback = {
          'access': x,
          'tag': f'Tag = {acc_tag:0{tag_bits}b}',
          'offset': f'Offset = {acc_off:0{block_bits}b}',
        }

    hit = False
    block_data = None
    for way in range(ways):
      if CACHE[acc_idx]["valid"][way] == 1 and CACHE[acc_idx]["tags"][way] == acc_tag:
        hit = True
        block_data = CACHE[acc_idx]["blocks"][way][acc_off]

    writeback = update_cache(acc_tag, acc_idx, addr)
    access = {
      'address': str_address,
      'hit': hit,
      'data': block_data,
      'writeback': writeback,
    }
    access_table.append(access)
    feedback_table.append(feedback)

    index.append(acc_idx)
    tag.append(acc_tag)
  ### List of memory accesses and their hits/misses in cache. Will be used by pl-cache-access-table
  data['correct_answers'][f'{answers_name}_access'] = access_table
  data['params']['tio_sequence'] = feedback_table

  return