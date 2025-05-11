import random
import string
import math
from random import choice

CACHE = []


########
## Change percentages to 30% hit, 30% collision, 30% adjacent block, 10% random
########
def generate(data):

  # number of addresses to generate
  num_addr = 5

  # Generate cache parameters
  total_size_KB = random.randint(1,6)
  associativity = random.randint(0,2) # allow only 1 and 2-way set associativity and fully associative (associativity == 0), maybe change?
  offset_size = random.randint(5,7)

  if associativity == 0:
    CACHE.append({'tags':[]})
    index_size = 0
  elif associativity == 1:
    index_size = 10 + total_size_KB - offset_size
  elif associativity == 2:
    index_size = 10 + total_size_KB - offset_size - 1
  elif associativity > 2:
    index_size = 10 + total_size_KB - offset_size - 2
  tag_size = 32 - offset_size - index_size
  num_sets = 2**index_size
  block_size = 2**offset_size

  data['params']['cache_size'] = 2**total_size_KB
  data['params']['block_size'] = block_size

  if associativity == 0:
    data['params']['associativity'] = 'fully-associative'
  elif associativity == 1:
    data['params']['associativity'] = 'direct-mapped'
  else:
    data['params']['associativity'] = f'{associativity}-way set associative'


  #####
  ## Generate a set of unique addresses that can be re-used
  #####
  addresses = []
  if associativity == 0:     # Create num_addr + 1 tags for fully asccoicative cache
    tags = [0]*(num_addr+1)
    for x in range(num_addr+1):
      tags[x] = random.randint(0, (2**tag_size)-1)
    address_dict = {'idx': 0, 'tags': tags}
    addresses.append(address_dict)
  else:
    tags = [0]*(associativity+1) #             create num_addr indexes
    for x in range(num_addr):
      acc_idx = random.randint(0, num_sets-1)
      for y in range(associativity+1):  #      for each index create associativity + 1 tags
        tags[y] = random.randint(0, (2**tag_size)-1)

      address_dict = {'idx': acc_idx, 'tags': tags}
      addresses.append(address_dict)

  # choose first address for access
  addr_choice = choice(addresses)
  acc_idx = addr_choice['idx']
  acc_tag = choice(addr_choice['tags'])
  acc_off = random.randint(0, block_size-1)

  address = (acc_tag * num_sets + acc_idx) * 2**offset_size + acc_off
  hex_address = '{0:#0{1}x}'.format(address, 10)

  access_table = []
  tio_sequence = []

  access = {
    'access': 0,
    'address': hex_address,
    'hit': False,
    'tag': hex(acc_tag),
    'index': hex(acc_idx),
    'text': 'Miss (Invalid)',
  }

  access_table.append(access)

  if associativity == 0:
    CACHE[0]['tags'].append(acc_tag)
  else:
    cache_entry = {'idx': acc_idx, 'tags': [acc_tag]}
    CACHE.append(cache_entry)


  # handle different associativity separately
  if associativity == 0:
    for x in range(num_addr):
      hit_choice = random.randint(0,9)
      if hit_choice <= 4: # 50% chance of hit
        acc_idx = 0
        acc_tag = random.choice(CACHE[0]['tags'])
        acc_off = random.randint(0, block_size-1)

        address = acc_tag * block_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': True,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Hit'
        }
      else:
        acc_idx = 0

        # Get a random tag that is not already in the cache
        acc_tag = CACHE[acc_idx]['tags'][0]
        while acc_tag in CACHE[acc_idx]['tags']:
          acc_tag = choice(addresses[0]['tags'])
        CACHE[0]['tags'].append(acc_tag)

        acc_off = random.randint(0, (2**offset_size)-1)

        address = acc_tag * block_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': False,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Miss (Invalid)'
        }
  else:
    for x in range(num_addr): # add choice of same index different tag
      hit_choice = random.randint(0,9)# random.randint(0,9)

      if hit_choice <= 3: # 40% chance of hit

        if associativity == 1:
          cache_block = choice(CACHE)   # choose a random cache block
          acc_tag = cache_block['tags'][0] # choose a random tag in cache block
          acc_idx = cache_block['idx']
        else:
          cache_block = choice(CACHE)   # choose a random cache block
          acc_tag = choice(cache_block['tags']) # choose a random tag in cache block
          acc_idx = cache_block['idx']

          update_assoc(acc_idx, acc_tag, associativity)

        acc_off = random.randint(0, block_size-1)

        address = (acc_tag * num_sets + acc_idx) * block_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': True,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Hit'
        }

      elif hit_choice > 3 and hit_choice <= 7: # 30% chance of collision

        c_idx = random.randint(0,len(CACHE)-1) # choose a random cache block
        cache_block = CACHE[c_idx]
        acc_idx = cache_block['idx']

        addr_idx = 0
        for addr_idx in range(associativity+1):
          if acc_idx == addresses[addr_idx]:
            break

        acc_tag = CACHE[c_idx]['tags'][0]
        while acc_tag in CACHE[c_idx]['tags']:
          acc_tag = choice(addresses[addr_idx]['tags'])
        if associativity == 1:
          CACHE[c_idx]['tags'][0] = acc_tag
        else:
          update_assoc(acc_idx, acc_tag, associativity)

        acc_off = random.randint(0, block_size-1)

        address = (acc_tag * num_sets + acc_idx) * block_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': False,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Miss (Tag Mismatch)'
        }

      elif hit_choice > 7 and hit_choice <= 9: # 30% chance of same tag, different index
        cache_block = choice(CACHE) # choose a random cache element
        acc_tag = choice(cache_block['tags'])
        acc_idx = CACHE[0]['idx']
        while idx_in_cache(acc_idx):
          acc_idx = random.randint(0,2**index_size - 1)

        if associativity == 1:
          update_direct(acc_idx, acc_tag)
        else:
          update_assoc(acc_idx, acc_tag, associativity)

        acc_off = random.randint(0, block_size-1)

        address = (acc_tag * num_sets + acc_idx) * block_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': False,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Miss (Invalid)'
        }

      else: # 0% chance of random new address that's a miss, but leaving here in case we want the option later
        acc_tag = random.randint(0, (2**tag_size)-1)
        acc_idx = random.randint(0, num_sets-1)
        acc_off = random.randint(0, (2**offset_size)-1)

        address = (acc_tag * num_sets + acc_idx) * 2**offset_size + acc_off
        hex_address = '{0:#0{1}x}'.format(address, 10)

        access = {
          'access': x+1,
          'address': hex_address,
          'hit': False,
          'tag': hex(acc_tag),
          'index': hex(acc_idx),
          'text': 'Miss (Invalid)'
        }

        if associativity == 0:
          CACHE[0]['tags'].append(acc_tag)
        elif associativity == 1:
          update_direct(acc_idx, acc_tag)
        else:
          update_assoc(acc_idx, acc_tag, associativity)

      access_table.append(access)


  data['params']['access_table'] = access_table

  data['correct_answers']['cache_access'] = access_table
  data['correct_answers']['cache_access2'] = access_table


def update_direct(acc_idx, acc_tag):
  cache_entry = {'idx': acc_idx, 'tags': [acc_tag]}
  CACHE.append(cache_entry)

def update_assoc(acc_idx, acc_tag, associativity):
  idx_exists = False # determine if acc_idx has been accessed before

  # Find index of current memory access in CACHE array
  for x in range(len(CACHE)):
    if CACHE[x]['idx'] == acc_idx:
      temp_idx = x
      idx_exists = True
  if not idx_exists: # if idx doesn't exist, create it
    cache_entry = {'idx': acc_idx, 'tags': [acc_tag]}
    CACHE.append(cache_entry)
  elif len(CACHE[temp_idx]['tags']) < associativity: # if idx exists but some ways are empty, fill next way
    hit_way = False # found hit in a way flag
    for way in range(len(CACHE[temp_idx]['tags'])): # if idx exists, find hit_way or miss
      if CACHE[temp_idx]['tags'][way] == acc_tag:
        hit_way = True
        break
    if hit_way:
      while way < len(CACHE[temp_idx]['tags']) - 1:
        CACHE[temp_idx]['tags'][way] = CACHE[temp_idx]['tags'][way+1]
        way += 1
      CACHE[temp_idx]['tags'][way] = acc_tag
    else:
      CACHE[temp_idx]['tags'].append(acc_tag)
  else:
    hit_way = False # found hit in a way flag
    for way in range(associativity): # if idx exists and ways are full, find hit_way
      if CACHE[temp_idx]['tags'][way] == acc_tag:
        hit_way = True
        break

    if hit_way: # if hit found in a way, reorder tags, LRU tag is in CACHE[temp_idx]['tags'][0]
      while way < associativity - 1:
        CACHE[temp_idx]['tags'][way] = CACHE[temp_idx]['tags'][way+1]
        way += 1
      CACHE[temp_idx]['tags'][way] = acc_tag
    else: # if miss, replace LRU (CACHE[temp_idx]['tags'][0])
      way = 0
      while way < associativity - 1:
        CACHE[temp_idx]['tags'][way] = CACHE[temp_idx]['tags'][way+1]
        way += 1
      CACHE[temp_idx]['tags'][way] = acc_tag

def idx_in_cache(acc_idx):
  for x in range(len(CACHE)):
    if CACHE[x]['idx'] == acc_idx:
      return True
  return False
