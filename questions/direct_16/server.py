import random 
import string
import math
from random import choice
from cache_tables import generate_cache

def generate(data): 
  # number of addresses to generate
  NUM_ADDR = 16
  addr_bits = 8
  set_bits = 4
  block_bits = 2

  address_list = []
  for x in range(NUM_ADDR):
    if x % 4 == 0: # get new address every 4 accesses
      # Get address of mem access and then parse
      acc_addr = random.randint(0,2**(addr_bits-2) - 1) * 4 # make addr a multiple of 4 (i.e., offset 0)

    acc_off = random.randint(0,2**block_bits-1)

    address_list.append(acc_addr+acc_off)

  generate_cache(data, 'cache', 1, set_bits, address_list=address_list,
                      addr_bits = addr_bits,
                      block_bits = block_bits,
                      base = 'bin',
                      min_hits = 1,
                      min_miss = 1,
                )
