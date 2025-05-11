from cache_tables import generate_cache

def generate(data):
    # generate_cache(data, answers_name, num_ways,
    #                 index_bits,
    #                 num_addr,
    #                 addr_bits = 5,
    #                 block_bits = 1,
    #                 show_valid = False,
    #                 empty_cache = False)

    generate_cache(data, 'cache', 1, 2, 6,
                        addr_bits = 4,
                        block_bits = 1,
                        min_hits = 2,
                        show_valid = True,
                        partial_empty = True)
