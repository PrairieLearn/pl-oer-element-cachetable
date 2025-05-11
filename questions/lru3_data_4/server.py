from cache_tables import generate_cache
import random

def generate(data):
    # generate_cache(data, answers_name, num_ways,
    #                 index_bits,
    #                 num_addr,
    #                 addr_bits = 5,
    #                 block_bits = 1,
    #                 show_valid = False,
    #                 partial_cache = False)

    generate_cache(data, 'cache', set_bits=1, ways=3, num_addr=4, addr_bits=5, block_bits=1, base=random.choice(['hex','bin']))
    if data['params']['display_base'] == 'bin':
        data['params']['index_fixed_width'] = 5
    else:
        data['params']['index_fixed_width'] = 2
