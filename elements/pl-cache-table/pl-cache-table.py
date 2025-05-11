import random
import re
from enum import Enum
from typing import Any

import chevron
import lxml.html
import prairielearn as pl
from typing_extensions import assert_never

CORRECT_ANSWER_DEFAULT = None
BLOCK_BITS_DEFAULT = 1
SHOW_PERCENTAGE_SCORE_DEFAULT = True
SHOW_PARTIAL_SCORE_DEFAULT = True
IS_MATERIAL_DEFAULT = False
GRADE_MODE_DEFAULT = 'blocks'
DISPLAY_BASE_DEFAULT = 'hex'
SHOW_DATA_DEFAULT = True
SHOW_VALID_DEFAULT = False
SHOW_DIRTY_DEFAULT = False
TAG_WIDTH_DEFAULT = 40
WEIGHT_DEFAULT = '1'

CACHE_TABLE_MUSTACHE_TEMPLATE_NAME = 'pl-cache-table.mustache'


def prepare(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    required_attribs = ['answers-name', 'set-bits', 'num-ways']
    optional_attribs = [
        'block-bits',
        'show-valid',
        'show-data',
        'show-dirty',
        'grade-mode',
        'display-base',
        'tag-width',
        'show-partial-score',
        'show-percentage-score',
        'is-material',
        'weight',
    ]
    pl.check_attribs(element, required_attribs, optional_attribs)

    name = pl.get_string_attrib(element, 'answers-name')
    pl.check_answers_names(data, name)

    #Determine number of sets in cache
    set_bits = int(pl.get_string_attrib(element, 'set-bits'))
    if set_bits < 0:
        raise ValueError(
            f'The number of bits for the set index must be 0 or greater.'
        )

    num_sets = 2**set_bits

    num_ways = int(pl.get_string_attrib(element, 'num-ways'))
    if num_ways <= 0:
        raise ValueError(
            f'The number of ways for the cache must be 1 or greater.'
        )

    block_bits = int(pl.get_string_attrib(element, 'block-bits', BLOCK_BITS_DEFAULT))
    show_valid = pl.get_boolean_attrib(element, 'show-valid', SHOW_VALID_DEFAULT)
    show_data = pl.get_boolean_attrib(element, 'show-data', SHOW_DATA_DEFAULT)
    display_base = pl.get_string_attrib(element, 'display-base', DISPLAY_BASE_DEFAULT)

    if display_base != 'hex' and display_base != 'bin':
        raise ValueError(
            f'base must be "hex" or "bin"'
        )
    
    try:
        initial_cache = data['params'][name]
    except AttributeError:
        print(f"Initial cache configuration not found in data['params'][{name}]")
    try:
        final_cache = data['correct_answers'][name]
    except AttributeError:
        print(f"Final cache configuration not found in data['correct_answers'][{name}]")

    allowed_characters = '0123456789abcdef'

    for i in range(num_sets):
        for j in range(num_ways):
            # remove white space from students' answers
            try:
                tag = final_cache[i]['tags'][j]
            except:
                raise AttributeError('Tag value missing for index {i} and way{j}.')

            clean_tag = tag.replace('0x', '').replace(' ', '').lower()
            if not all(char in allowed_characters for char in clean_tag):
                raise ValueError('Tag for index {i} and way {j} must not have characters besides 0-9, a-f, and "0x".')

            if show_valid:
                try:
                    valid = final_cache[i]['valid'][j]
                except:
                    raise AttributeError('Tag value missing for index {i} and way{j}.')

                clean_valid = valid.replace(' ', '').lower()
                if not all(char in '01' for char in clean_valid):
                    raise ValueError('Valid for index {i} and way {j} must be 0 or 1.')

            if show_data:
                for k in range(2**block_bits):
                    try:
                        bdata = final_cache[i]['blocks'][j][k]
                    except:
                        raise AttributeError('Data value missing for index {i} and way{j} and offset{k}.')

                    clean_data = bdata.replace('0x', '').replace(' ', '').lower()
                    if not all(char in allowed_characters for char in clean_data):
                        raise ValueError('Data for index {i} and way {j} and offset {k} must not have characters besides 0-9, a-f, and "0x".')

            if num_ways > 1:
                try:
                    lru = final_cache[i]['lru'][j]
                except:
                    raise AttributeError('LRU value missing for index {i}.')

                clean_lru = lru.replace(' ', '').lower()
                if not all(char in allowed_characters for char in clean_lru):
                    raise ValueError('LRU for index {i} must not have characters besides 0-9.')
    
def render(element_html: str, data: pl.QuestionData) -> str:

    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')
    # Get the output name

    show_partial_score = pl.get_boolean_attrib(
        element, 'show-partial-score', SHOW_PARTIAL_SCORE_DEFAULT
    )  # Default to False if not specified

    show_percentage_score = pl.get_boolean_attrib(
        element, 'show-percentage-score', SHOW_PERCENTAGE_SCORE_DEFAULT
    )  # Default to False if not specified

    #get number of sets
    set_bits = int(pl.get_string_attrib(element, 'set-bits'))
    num_sets = 2**set_bits

    block_bits = int(pl.get_string_attrib(element, 'block-bits'))

    num_ways = int(pl.get_string_attrib(element, 'num-ways'))

    fully_assoc = False
    if set_bits == 0:
        fully_assoc = True

    grade_mode = pl.get_string_attrib(element, 'grade-mode', GRADE_MODE_DEFAULT)

    #create a list of ways to render table header. A bit hacky
    way_list = []
    for i in range(num_ways):
        way_list.append({'number': i})

    is_material = pl.get_boolean_attrib(element, 'is-material', IS_MATERIAL_DEFAULT)
    show_data = pl.get_boolean_attrib(element, 'show-data', SHOW_DATA_DEFAULT)
    show_dirty = pl.get_boolean_attrib(element, 'show-dirty', SHOW_DIRTY_DEFAULT)
    show_valid = pl.get_boolean_attrib(element, 'show-valid', SHOW_VALID_DEFAULT)
    display_base = pl.get_string_attrib(element, 'display-base', DISPLAY_BASE_DEFAULT)
    display_base = display_base.lower()
    tag_width = int(pl.get_string_attrib(element, 'tag-width', TAG_WIDTH_DEFAULT))
    if tag_width != TAG_WIDTH_DEFAULT and display_base == 'hex':
        tag_width = 60

    initial_cache = data['params'][name]
    final_cache = data['correct_answers'][name]

    #create a list of offsets to render table header
    if show_data:
        block_list = []
        for i in range(2**block_bits):
            block_list.append({'offset': f'{i:0x}' if display_base == 'hex' else f'{i:0{block_bits}b}'})
    else:
        block_list = None

    #determine number of columns for Way numbering to span
    way_display_width = 1 #must have at least the tag at minimum
    if show_data:
        way_display_width += 2**block_bits #increase columns by width of cache blocks
    if show_valid:
        way_display_width += 1 #increase column by 1 to include valid
    if show_dirty:
        way_display_width += 1 #increase column by 1 to include dirty

    #construct a cache_sets array to store all cache information
    prefill = {}
    cache_sets = []
    for i in range(num_sets):
        #initialize set
        cache_set = {
            'index': f'{i:0x}' if display_base == 'hex' else f'{i:0{set_bits}b}',
            'ways': [], #array of blocks in each way
            'all_lru_correct': False,
            'all_lru_incorrect': False,
        }

        for j in range(num_ways):
            tag_name = f'{name}_tag{i}_{j}'
            valid_name = f'{name}_valid{i}_{j}'
            dirty_name = f'{name}_dirty{i}_{j}'
            way = {
                'initial_tag': initial_cache[i]['tags'][j], # update to include initial tag, raw_submitted_tag, and 
                'final_tag': final_cache[i]['tags'][j], # update to include initial tag, raw_submitted_tag, and 
                'tag_name': tag_name,
                'raw_sub_tag': data['raw_submitted_answers'].get(tag_name, None),
                'tag_input_error': data['format_errors'].get(tag_name, None),
                'valid_input_error': data['format_errors'].get(valid_name, None),
                'dirty_input_error': data['format_errors'].get(dirty_name, None),
                'block_correct': False,
                'block_incorrect': False,
                'tag_correct': False,
                'tag_incorrect': False,
                'valid_correct': False,
                'valid_incorrect': False,
                'dirty_correct': False,
                'dirty_incorrect': False,
            }
            tag_score = data['partial_scores'].get(f'{name}_tag{i}_{j}')
            if tag_score != None and grade_mode != 'blocks' and show_partial_score:
                if tag_score['score'] == 1:
                    way['tag_correct'] = True
                else:
                    way['tag_incorrect'] = True

            block_score = data['partial_scores'].get(f'{name}_block{i}_{j}')
            if block_score != None and grade_mode == 'blocks' and show_partial_score:
                if block_score['score'] == 1:
                    way['block_correct'] = True
                else:
                    way['block_incorrect'] = True

            if show_valid:
                way.update({'initial_valid': initial_cache[i]['valid'][j]})
                way.update({'final_valid': final_cache[i]['valid'][j]})
                way.update({'valid_name': valid_name})
                way.update({'raw_sub_valid': data['raw_submitted_answers'].get(valid_name)})
                valid_score = data['partial_scores'].get(f'{name}_valid{i}_{j}')
                if valid_score != None and grade_mode != 'blocks' and show_partial_score:
                    if valid_score['score'] == 1:
                        way['valid_correct'] = True
                    else:
                        way['valid_incorrect'] = True

            if show_dirty:
                way.update({'initial_dirty': initial_cache[i]['dirty'][j]})
                way.update({'final_dirty': final_cache[i]['dirty'][j]})
                way.update({'dirty_name': dirty_name})
                way.update({'raw_sub_dirty': data['raw_submitted_answers'].get(dirty_name)})
                dirty_score = data['partial_scores'].get(f'{name}_dirty{i}_{j}')
                if dirty_score != None and grade_mode != 'blocks' and show_partial_score:
                    if dirty_score['score'] == 1:
                        way['dirty_correct'] = True
                    else:
                        way['dirty_incorrect'] = True

            if show_data:
                block = []
                for k in range(2**block_bits):
                    data_name = f'{name}_data{i}_{j}_{k}'
                    byte = {
                        'initial_data': initial_cache[i]['blocks'][j][k],
                        'final_data': final_cache[i]['blocks'][j][k],
                        'data_name': data_name,
                        'raw_sub_data': data['raw_submitted_answers'].get(data_name),
                        'data_input_error': data['format_errors'].get(data_name, None),
                        'data_correct': False,
                        'data_incorrect': False,
                        'last_data': False,
                    }
                    data_score = data['partial_scores'].get(f'{name}_data{i}_{j}_{k}', None)
                    if data_score != None and grade_mode != 'blocks' and show_partial_score:
                        if data_score['score'] == 1:
                            byte['data_correct'] = True
                        else:
                            byte['data_incorrect'] = True
                    if k == 2**block_bits - 1:
                        byte['last_data'] = True

                    block.append(byte)

                way.update({'block': block})
                
            cache_set['ways'].append(way)

        has_lru = True
        if num_ways > 1:
            lru = []
            for j in range(num_ways):
                lru_name = f'{name}_lru{i}_{j}'
                lru_state = {
                    'lru_name': lru_name, 
                    'initial_lru': initial_cache[i]['lru'][j], 
                    'final_lru': final_cache[i]['lru'][j],
                    'raw_sub_lru': data['raw_submitted_answers'].get(lru_name),
                    'lru_input_error': data['format_errors'].get(lru_name, None),
                    'lru_correct': False,
                    'lru_incorrect': False,
                }
                lru_score = data['partial_scores'].get(f'{name}_lru{i}_{j}')
                if lru_score != None and grade_mode != 'blocks' and show_partial_score:
                    if lru_score['score'] == 1:
                        lru_state['lru_correct'] = True
                    else:
                        lru_state['lru_incorrect'] = True
                if j < (num_ways - 1):
                    lru_state.update({'comma': True})

                lru.append(lru_state)

            block_score = data['partial_scores'].get(f'{name}_lru_block{i}')
            if block_score != None and grade_mode == 'blocks' and show_partial_score:
                if block_score['score'] == 1:
                    cache_set['all_lru_correct'] = True
                else:
                    cache_set['all_lru_incorrect'] = True

            cache_set.update({'lru': lru})
        else:
            has_lru = False

        cache_sets.append(cache_set)


    #print(cache_sets)
    correct = False
    partial = False
    incorrect = False

    partial_score = data['partial_scores'].get(name)
    if partial_score != None:
        score = round(partial_score['score'] * 100, 2)
        if score == 100:
            correct = True
        elif score > 0:
            partial = True
        else:
            incorrect = True
    else:
        score = None

    grade_info = ''
    if grade_mode == 'blocks':
        grade_info = 'Reset button will reset the contents of the cache to the initial state for this problem.<br>Cache is graded per cache block and per LRU FSM. If any cell in a block or LRU FSM is incorrect, then entire block is marked as incorrect (solid outline). Dotted outline indicates a block is correct'
    elif grade_mode == 'cells':
        grade_info = 'Reset button will reset the contents of the cache to the initial state for this problem.<br>Each text box in the cache will be graded independently. Correct cells have a solid outline, incorrect cells have a dotted outline.'
    else:
        grade_info = 'Reset button will reset the contents of the cache to the initial state for this problem.<br>Each text box in the cache will be graded independently. If any cell is incorrect, no credit will be awarded'

    if not show_partial_score:
        grade_info += '<br>Partial score information will not be shown'

    if not show_percentage_score:
        grade_info += '<br>Total percentage score for this table will not be shown'

    # Get template
    with open(CACHE_TABLE_MUSTACHE_TEMPLATE_NAME, 'r', encoding='utf-8') as f:
        template = f.read()
    if data['panel'] == 'question':
        grading_text = 'PLACEHOLDER'
        info_params = {
            'format': True,
            'grading_text': grading_text,
        }
        info = chevron.render(template, info_params)
        html_params = {
            'question': True,
            'name': name,
            'info': info,
            'uuid': pl.get_uuid(),
            'cache_sets': cache_sets,
            'num_sets': num_sets,
            'way_list': way_list,
            'block_list': block_list,
            'prefill': prefill,
            'score': score,
            'show_valid': show_valid,
            'show_dirty': show_dirty,
            'way_display_width': way_display_width,
            'blocks': True if grade_mode == 'blocks' and score != None else False,
            'has_lru': has_lru,
            'fully_assoc': fully_assoc,
            'all_correct': correct,
            'all_incorrect': incorrect,
            'all_partial': partial,
            'grade-info': grade_info,
            'tag_width': tag_width,
            'is_material': is_material,
            'show-percentage-score': show_percentage_score,
        }
        return chevron.render(template, html_params)

    if data['panel'] == 'submission':
        html_params = {
            'submission': True,
            'name': name,
            'uuid': pl.get_uuid(),
            'cache_sets': cache_sets,
            'num_sets': num_sets,
            'way_list': way_list,
            'block_list': block_list,
            'show_valid': show_valid,
            'show_dirty': show_dirty,
            'score': score,
            'way_display_width': way_display_width,
            'blocks': True if grade_mode == 'blocks' and score != None else False,
            'has_lru': has_lru,
            'fully_assoc': fully_assoc,
            'all_correct': correct,
            'all_incorrect': incorrect,
            'all_partial': partial,
            'is_material': is_material,
            'show-percentage-score': show_percentage_score,
        }
        return chevron.render(template, html_params)

    if data['panel'] == 'answer':
        html_params = {
            'answer': True,
            'name': name,
            'uuid': pl.get_uuid(),
            'cache_sets': cache_sets,
            'num_sets': num_sets,
            'way_list': way_list,
            'block_list': block_list,
            'blocks': True if grade_mode == 'blocks' else False,
            'show_valid': show_valid,
            'show_dirty': show_dirty,
            'way_display_width': way_display_width,
            'has_lru': has_lru,
            'fully_assoc': fully_assoc,
            'is_material': is_material,
        }
        return chevron.render(template, html_params)

def parse(element_html: str, data: pl.QuestionData) -> None:

    element = lxml.html.fragment_fromstring(element_html)
    
    is_material = pl.get_boolean_attrib(element, 'is-material', IS_MATERIAL_DEFAULT)
    if is_material:
        return

    name = pl.get_string_attrib(element, 'answers-name')

    set_bits = int(pl.get_string_attrib(element, 'set-bits'))
    num_sets = 2**set_bits

    block_bits = int(pl.get_string_attrib(element, 'block-bits'))

    num_ways = int(pl.get_string_attrib(element, 'num-ways'))

    show_valid = pl.get_boolean_attrib(element, 'show-valid', SHOW_VALID_DEFAULT)
    show_dirty = pl.get_boolean_attrib(element, 'show-dirty', SHOW_DIRTY_DEFAULT)
    show_data = pl.get_boolean_attrib(element, 'show-data', SHOW_DATA_DEFAULT)

    allowed_characters = '0123456789abcdef'

    for i in range(num_sets):
        for j in range(num_ways):
            # remove white space from students' answers
            tag = data['raw_submitted_answers'].get(f'{name}_tag{i}_{j}')
            clean_tag = tag.replace('0x', '').replace(' ', '').lower()
            if clean_tag == '' and data['params'][name][i]['tags'][j] != '':
                data['format_errors'][f'{name}_tag{i}_{j}'] = 'Tag cannot be empty if it starts with a value. Initial value has been re-entered'

            if not all(char in allowed_characters for char in clean_tag):
                data['format_errors'][f'{name}_tag{i}_{j}'] = 'Tag must not have characters besides 0-9, a-f, and "0x".'
            else:
                data['submitted_answers'][f'{name}_tag{i}_{j}'] = clean_tag


            if show_valid:
                valid = data['raw_submitted_answers'].get(f'{name}_valid{i}_{j}')
                clean_valid = valid.replace(' ', '').lower()
                if clean_valid == '' and data['params'][name][i]['valid'][j] != '':
                    data['format_errors'][f'{name}_valid{i}_{j}'] = 'Valid bit cannot be empty if it starts with a value. Initial value has been re-entered'
                if not all(char in '01' for char in clean_valid):
                    data['format_errors'][f'{name}_valid{i}_{j}'] = 'Valid must be 0 or 1.'
                else:
                    data['submitted_answers'][f'{name}_valid{i}_{j}'] = clean_valid

            if show_dirty:
                dirty = data['raw_submitted_answers'].get(f'{name}_dirty{i}_{j}')
                clean_dirty = dirty.replace(' ', '').lower()
                if clean_dirty == '' and data['params'][name][i]['dirty'][j] != '':
                    data['format_errors'][f'{name}_dirty{i}_{j}'] = 'Valid bit cannot be empty if it starts with a value. Initial value has been re-entered'
                if not all(char in '01' for char in clean_dirty):
                    data['format_errors'][f'{name}_dirty{i}_{j}'] = 'Valid must be 0 or 1.'
                else:
                    data['submitted_answers'][f'{name}_dirty{i}_{j}'] = clean_dirty

            if show_data:
                for k in range(2**block_bits):
                    bdata = data['raw_submitted_answers'].get(f'{name}_data{i}_{j}_{k}')
                    clean_data = bdata.replace('0x', '').replace(' ', '').lower()
                    if clean_data == '' and data['params'][name][i]['blocks'][j][k] != '':
                        data['format_errors'][f'{name}_data{i}_{j}_{k}'] = 'Data cannot be empty if it starts with a value. Initial value has been re-entered'
                    if not all(char in allowed_characters for char in clean_data):
                        data['format_errors'][f'{name}_data{i}_{j}_{k}'] = 'Data must not have characters besides 0-9, a-f, and "0x".'
                    else:
                        data['submitted_answers'][f'{name}_data{i}_{j}_{k}'] = clean_data

            if num_ways > 1:
                lru = data['raw_submitted_answers'].get(f'{name}_lru{i}_{j}')
                clean_lru = lru.replace(' ', '').lower()
                if clean_lru == '' and data['params'][name][i]['lru'][j] != '':
                    data['format_errors'][f'{name}_lru{i}_{j}'] = 'Valid bit cannot be empty if it starts with a value. Initial value has been re-entered'
                if not all(char in allowed_characters for char in clean_lru):
                    data['format_errors'][f'{name}_lru{i}_{j}'] = 'LRU must not have characters besides 0-9.'
                else:
                    data['submitted_answers'][f'{name}_lru{i}_{j}'] = clean_lru

    return
    
def grade(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)

    is_material = pl.get_boolean_attrib(element, 'is-material', IS_MATERIAL_DEFAULT)
    if is_material:
        return

    name = pl.get_string_attrib(element, 'answers-name')

    grade_mode = pl.get_string_attrib(element, 'grade-mode', GRADE_MODE_DEFAULT)

    initial_cache = data['params'][name]
    final_cache = data['correct_answers'][name]
    sub_cache = data['submitted_answers']

    set_bits = int(pl.get_string_attrib(element, 'set-bits'))
    num_sets = 2**set_bits

    block_bits = int(pl.get_string_attrib(element, 'block-bits'))

    num_ways = int(pl.get_string_attrib(element, 'num-ways'))

    show_valid = pl.get_boolean_attrib(element, 'show-valid', SHOW_VALID_DEFAULT)
    show_dirty = pl.get_boolean_attrib(element, 'show-dirty', SHOW_DIRTY_DEFAULT)
    show_data = pl.get_boolean_attrib(element, 'show-data', SHOW_DATA_DEFAULT)

    weight = int(pl.get_string_attrib(element, 'weight', WEIGHT_DEFAULT))

    allowed_characters = '0123456789abcdef'

    num_blocks = num_sets*(num_ways)
    if num_ways > 1:
        num_blocks += num_sets # one more set of blocks for LRUs

    num_cells_mult = 1 # at least 1 bit for tag
    if show_data:
        num_cells_mult += 2**block_bits
    if show_valid:
        num_cells_mult += 1
    if show_dirty:
        num_cells_mult += 1
    if num_ways > 1:
        num_cells_mult += 1
    num_cells = num_sets*num_ways*num_cells_mult

    num_blocks_changed = 0
    num_cells_changed = 0

    changed_blocks_correct = 0
    same_blocks_correct = 0
    changed_cells_correct = 0
    same_cells_correct = 0

    for i in range(num_sets):
        lru_block_changed = False
        lru_block_correct = True
        for j in range(num_ways):
            block_changed = False
            block_correct = True
            # remove white space from students' answers
            initial_tag = initial_cache[i]['tags'][j].replace('0x', '').replace(' ', '').lower()
            final_tag = final_cache[i]['tags'][j].replace('0x', '').replace(' ', '').lower()
            sub_tag = sub_cache.get(f'{name}_tag{i}_{j}')
            cell_changed = 0
            if initial_tag != final_tag:
                cell_changed = 1
                block_changed = True
            num_cells_changed += cell_changed
            if sub_tag == final_tag:
                data['partial_scores'][f'{name}_tag{i}_{j}'] = {
                    'score': 1,
                    'weight': 0,
                }
                changed_cells_correct += cell_changed
                same_cells_correct += (1-cell_changed)
            else:
                block_correct = False
                data['partial_scores'][f'{name}_tag{i}_{j}'] = {
                    'score': 0,
                    'weight': 0,
                }

            if show_valid:
                initial_valid = initial_cache[i]['valid'][j].replace(' ', '').lower()
                final_valid = final_cache[i]['valid'][j].replace(' ', '').lower()
                sub_valid = sub_cache.get(f'{name}_valid{i}_{j}')
                cell_changed = 0
                if initial_valid != final_valid:
                    cell_changed = 1
                    block_changed = True
                num_cells_changed += cell_changed
                if sub_valid == final_valid:
                    data['partial_scores'][f'{name}_valid{i}_{j}'] = {
                        'score': 1,
                        'weight': 0,
                    }
                    changed_cells_correct += cell_changed
                    same_cells_correct += (1-cell_changed)
                else:
                    data['partial_scores'][f'{name}_valid{i}_{j}'] = {
                        'score': 0,
                        'weight': 0,
                    }
                    block_correct = False

            if show_dirty:
                initial_dirty = initial_cache[i]['dirty'][j].replace(' ', '').lower()
                final_dirty = final_cache[i]['dirty'][j].replace(' ', '').lower()
                sub_dirty = sub_cache.get(f'{name}_dirty{i}_{j}')
                cell_changed = 0
                if initial_dirty != final_dirty:
                    cell_changed = 1
                    block_changed = True
                num_cells_changed += cell_changed
                if sub_dirty == final_dirty:
                    data['partial_scores'][f'{name}_dirty{i}_{j}'] = {
                        'score': 1,
                        'weight': 0,
                    }
                    changed_cells_correct += cell_changed
                    same_cells_correct += (1-cell_changed)
                else:
                    data['partial_scores'][f'{name}_dirty{i}_{j}'] = {
                        'score': 0,
                        'weight': 0,
                    }
                    block_correct = False

            if show_data:
                for k in range(2**block_bits):
                    initial_data = initial_cache[i]['blocks'][j][k].replace('0x', '').replace(' ', '').lower()
                    final_data = final_cache[i]['blocks'][j][k].replace('0x', '').replace(' ', '').lower()
                    sub_data = sub_cache.get(f'{name}_data{i}_{j}_{k}')
                    cell_changed = 0
                    if initial_data != final_data:
                        cell_changed = 1
                        block_changed = True
                    num_cells_changed += cell_changed
                    if sub_data == final_data:
                        data['partial_scores'][f'{name}_data{i}_{j}_{k}'] = {
                            'score': 1,
                            'weight': 0,
                        }
                        changed_cells_correct += cell_changed
                        same_cells_correct += (1-cell_changed)
                    else:
                        data['partial_scores'][f'{name}_data{i}_{j}_{k}'] = {
                            'score': 0,
                            'weight': 0,
                        }
                        block_correct = False

            if block_correct:
                data['partial_scores'][f'{name}_block{i}_{j}'] = {
                    'score': 1,
                    'weight': 0,
                }
                if block_changed:
                    num_blocks_changed += 1
                    changed_blocks_correct += 1
                else:
                    same_blocks_correct += 1
            else:
                data['partial_scores'][f'{name}_block{i}_{j}'] = {
                    'score': 0,
                    'weight': 0,
                }
                if block_changed:
                    num_blocks_changed += 1

            if num_ways > 1:
                initial_lru = initial_cache[i]['lru'][j]
                initial_lru = initial_lru.replace(' ', '').lower()
                final_lru = final_cache[i]['lru'][j]
                final_lru = final_lru.replace(' ', '').lower()
                sub_lru = sub_cache.get(f'{name}_lru{i}_{j}')
                cell_changed = 0
                if initial_lru != final_lru:
                    cell_changed = 1
                    lru_block_changed = True
                num_cells_changed += cell_changed
                if sub_lru == final_lru:
                    data['partial_scores'][f'{name}_lru{i}_{j}'] = {
                        'score': 1,
                        'weight': 0,
                    }
                    changed_cells_correct += cell_changed
                    same_cells_correct += (1-cell_changed)
                else:
                    data['partial_scores'][f'{name}_lru{i}_{j}'] = {
                        'score': 0,
                        'weight': 0,
                    }
                    lru_block_correct = False


        if lru_block_correct:
            data['partial_scores'][f'{name}_lru_block{i}'] = {
                'score': 1,
                'weight': 0,
            }
            if lru_block_changed:
                num_blocks_changed += 1
                changed_blocks_correct += 1
            else:
                same_blocks_correct += 1
        else:
            data['partial_scores'][f'{name}_lru_block{i}'] = {
                'score': 0,
                'weight': 0,
            }
            if lru_block_changed:
                num_blocks_changed += 1

    #print(f'num_cells: {num_cells}, num_cells_changed: {num_cells_changed}, changed_cells_correct: {changed_cells_correct}, same_cells_correct: {same_cells_correct}')
    #print(f'num_blocks: {num_blocks}, num_blocks_changed: {num_blocks_changed}, changed_blocks_correct: {changed_blocks_correct}, same_blocks_correct: {same_blocks_correct}')
    if initial_cache == final_cache:
        if same_cells_correct == num_cells:
            data['partial_scores'][name] = {
                'score': 1,
                'weight': weight,
            }
        else:
            data['partial_scores'][name] = {
                'score': 0,
                'weight': weight,
            }
    elif grade_mode == 'blocks':
        score = changed_blocks_correct/num_blocks_changed
        if same_blocks_correct < num_blocks - num_blocks_changed:
            score = max(score - 0.5, 0)
        data['partial_scores'][name] = {
            'score': score,
            'weight': weight,
        }
    elif grade_mode == 'all-or-nothing':
        if num_cells == changed_cells_correct + same_cells_correct:
            data['partial_scores'][name] = {
                'score': 1,
                'weight': weight,
            }
        else:
            data['partial_scores'][name] = {
                'score': 0,
                'weight': weight,
            }            
    else:
        score = changed_cells_correct/num_cells_changed
        if same_cells_correct < num_cells - num_cells_changed:
            score = max(score - 0.5, 0)

        data['partial_scores'][name] = {
            'score': score,
            'weight': weight,
        }

    return


def test(element_html: str, data: pl.ElementTestData) -> None:
    return
